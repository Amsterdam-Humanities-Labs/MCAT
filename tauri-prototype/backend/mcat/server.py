"""
MCAT Backend Server for Tauri.

HTTP API that wraps the existing MCAT services:
- Project management (create, open, status)
- Processing (start, pause, resume, cancel, status)
- Run management (start, resume, complete, stats)
"""

import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Import directly from local modules (no sys.path hack needed)
from services.project_service import ProjectService
from services.run_service import RunService
from services.processing_service import ProcessingService
from models.project_state import ProjectState

DEFAULT_PORT = 9876
MAX_PORT_ATTEMPTS = 10


def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts}")


class MCATBackend:
    """Singleton backend state manager."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.project_service = ProjectService()
        self.run_service = RunService()
        self.processing_service: ProcessingService | None = None
        self.current_project: ProjectState | None = None
        self._initialized = True

    def set_project(self, project: ProjectState):
        """Set current project and initialize processing service."""
        self.current_project = project
        if self.processing_service:
            self.processing_service.cleanup()
        self.processing_service = ProcessingService(platform=project.platform)


class MCATHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCAT API."""

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, message: str, status: int = 400):
        """Send error response."""
        self._send_json({"error": message}, status)

    def _read_json_body(self) -> dict:
        """Read and parse JSON request body."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        return json.loads(body.decode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        path = urlparse(self.path).path
        backend = MCATBackend()

        routes = {
            "/health": self._health,
            "/project/status": self._project_status,
            "/process/status": self._process_status,
            "/run/stats": self._run_stats,
            "/run/interrupted": self._run_interrupted,
            "/results/combined": self._results_combined,
            "/logs": self._get_logs,
        }

        handler = routes.get(path)
        if handler:
            handler(backend)
        else:
            self._send_error("Not found", 404)

    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path
        backend = MCATBackend()

        try:
            body = self._read_json_body()
        except json.JSONDecodeError:
            self._send_error("Invalid JSON")
            return

        routes = {
            "/project/create": self._project_create,
            "/project/open": self._project_open,
            "/project/close": self._project_close,
            "/project/import-preview": self._import_preview,
            "/project/import-confirm": self._import_confirm,
            "/process/start": self._process_start,
            "/process/pause": self._process_pause,
            "/process/resume": self._process_resume,
            "/process/cancel": self._process_cancel,
            "/run/start": self._run_start,
            "/run/complete": self._run_complete,
            "/run/resume": self._run_resume,
            "/run/abandon": self._run_abandon,
            "/csv/load": self._csv_load,
            "/csv/detect-url-column": self._detect_url_column,
        }

        handler = routes.get(path)
        if handler:
            handler(backend, body)
        else:
            self._send_error("Not found", 404)

    # === Health ===

    def _health(self, backend: MCATBackend):
        """Health check endpoint."""
        self._send_json({
            "status": "ok",
            "has_project": backend.current_project is not None,
            "is_processing": backend.processing_service.is_processing() if backend.processing_service else False
        })

    # === Project endpoints ===

    def _project_status(self, backend: MCATBackend):
        """Get current project status."""
        if not backend.current_project:
            self._send_json({"project": None})
            return

        project = backend.current_project
        self._send_json({
            "project": {
                "name": project.name,
                "platform": project.platform,
                "path": str(project.project_path),
                "url_count": backend.project_service.get_url_count(project),
                "url_column": project.url_column,
                "runs": [
                    {
                        "id": r.id,
                        "status": r.status.value,
                        "started_at": r.started_at.isoformat() if r.started_at else None,
                        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                    }
                    for r in project.config.runs
                ]
            }
        })

    def _project_create(self, backend: MCATBackend, body: dict):
        """Create a new project."""
        required = ["name", "platform", "location", "csv_path", "url_column"]
        for field in required:
            if field not in body:
                self._send_error(f"Missing required field: {field}")
                return

        try:
            project = backend.project_service.create_project(
                name=body["name"],
                platform=body["platform"],
                location=Path(body["location"]),
                source_csv=Path(body["csv_path"]),
                url_column=body["url_column"],
                preserve_columns=body.get("preserve_columns", [])
            )
            backend.set_project(project)
            self._send_json({"success": True, "project_path": str(project.project_path)})
        except Exception as e:
            self._send_error(str(e))

    def _project_open(self, backend: MCATBackend, body: dict):
        """Open an existing project."""
        if "path" not in body:
            self._send_error("Missing required field: path")
            return

        try:
            project = backend.project_service.open_project(Path(body["path"]))
            backend.set_project(project)
            self._send_json({"success": True, "name": project.name})
        except Exception as e:
            self._send_error(str(e))

    def _project_close(self, backend: MCATBackend, body: dict):
        """Close current project."""
        if backend.processing_service:
            backend.processing_service.cleanup()
        backend.current_project = None
        backend.processing_service = None
        self._send_json({"success": True})

    # === Processing endpoints ===

    def _process_status(self, backend: MCATBackend):
        """Get processing status."""
        if not backend.processing_service:
            self._send_json({"status": "no_project"})
            return

        status = backend.processing_service.get_current_status()
        self._send_json({
            "state": status.state.value if status.state else "idle",
            "total": status.total_count,
            "processed": status.processed_count,
            "stats": status.stats,
            "action": status.current_action,
            "error": status.error_message
        })

    def _process_start(self, backend: MCATBackend, body: dict):
        """Start processing."""
        if not backend.current_project:
            self._send_error("No project open")
            return

        if not backend.processing_service:
            self._send_error("Processing service not initialized")
            return

        # Get URLs to process
        urls = body.get("urls")  # Optional: for resume

        try:
            # Create processing job from current project
            from models.processing_models import ProcessingJob
            from models.file_models import FileInfo, ColumnMapping
            import pandas as pd

            project = backend.current_project
            df = pd.read_csv(project.urls_csv_path)

            file_info = FileInfo(path=str(project.urls_csv_path))
            file_info.dataframe = df
            file_info.row_count = len(df)
            file_info.columns = list(df.columns)
            file_info.valid = True

            column_mapping = ColumnMapping()
            column_mapping.post_column = project.url_column

            job = ProcessingJob(
                file_info=file_info,
                column_mapping=column_mapping,
                platform=project.platform,
                output_folder=str(project.get_run_path(backend.run_service.generate_run_id())),
                save_screenshots=body.get("screenshots", False)
            )

            success = backend.processing_service.start_processing(job, urls=urls)
            self._send_json({"success": success})
        except Exception as e:
            self._send_error(str(e))

    def _process_pause(self, backend: MCATBackend, body: dict):
        """Pause processing."""
        if not backend.processing_service:
            self._send_error("No processing service")
            return

        success = backend.processing_service.pause_processing()
        self._send_json({"success": success})

    def _process_resume(self, backend: MCATBackend, body: dict):
        """Resume processing."""
        if not backend.processing_service:
            self._send_error("No processing service")
            return

        success = backend.processing_service.resume_processing()
        self._send_json({"success": success})

    def _process_cancel(self, backend: MCATBackend, body: dict):
        """Cancel processing."""
        if not backend.processing_service:
            self._send_error("No processing service")
            return

        success = backend.processing_service.cancel_processing()
        self._send_json({"success": success})

    # === Run endpoints ===

    def _run_start(self, backend: MCATBackend, body: dict):
        """Start a new run."""
        if not backend.current_project:
            self._send_error("No project open")
            return

        try:
            run = backend.run_service.start_run(
                backend.current_project,
                screenshots_enabled=body.get("screenshots", False)
            )
            self._send_json({"success": True, "run_id": run.id})
        except Exception as e:
            self._send_error(str(e))

    def _run_complete(self, backend: MCATBackend, body: dict):
        """Complete current run."""
        if not backend.current_project:
            self._send_error("No project open")
            return

        if not backend.current_project.current_run:
            self._send_error("No active run")
            return

        try:
            backend.run_service.complete_run(
                backend.current_project,
                backend.current_project.current_run
            )
            self._send_json({"success": True})
        except Exception as e:
            self._send_error(str(e))

    def _run_stats(self, backend: MCATBackend):
        """Get current run stats."""
        if not backend.current_project:
            self._send_json({"stats": None})
            return

        if not backend.current_project.current_run:
            self._send_json({"stats": None})
            return

        stats = backend.run_service.get_run_stats(
            backend.current_project,
            backend.current_project.current_run
        )
        self._send_json({"stats": stats})

    def _run_interrupted(self, backend: MCATBackend):
        """Check for interrupted runs."""
        if not backend.current_project:
            self._send_json({"has_interrupted": False})
            return

        try:
            interrupted = backend.current_project.config.get_interrupted_run()
            if interrupted:
                processed_count = backend.run_service.get_processed_count(
                    backend.current_project, interrupted
                )
                total_count = backend.project_service.get_url_count(backend.current_project)
                self._send_json({
                    "has_interrupted": True,
                    "run": {
                        "run_id": interrupted.id,
                        "processed": processed_count,
                        "total": total_count,
                        "remaining": total_count - processed_count
                    }
                })
            else:
                self._send_json({"has_interrupted": False})
        except Exception as e:
            self._send_json({"has_interrupted": False})

    def _run_resume(self, backend: MCATBackend, body: dict):
        """Resume an interrupted run."""
        if not backend.current_project:
            self._send_error("No project open")
            return

        run_id = body.get("run_id")
        if not run_id:
            self._send_error("Missing run_id")
            return

        try:
            run = backend.current_project.config.get_run(run_id)
            if not run:
                self._send_error(f"Run not found: {run_id}")
                return
            run, remaining = backend.run_service.resume_run(backend.current_project, run)
            self._send_json({"success": True, "remaining_urls": remaining})
        except Exception as e:
            self._send_error(str(e))

    def _run_abandon(self, backend: MCATBackend, body: dict):
        """Abandon an interrupted run."""
        if not backend.current_project:
            self._send_error("No project open")
            return

        run_id = body.get("run_id")
        if not run_id:
            self._send_error("Missing run_id")
            return

        try:
            run = backend.current_project.config.get_run(run_id)
            if not run:
                self._send_error(f"Run not found: {run_id}")
                return
            backend.run_service.abandon_run(backend.current_project, run)
            self._send_json({"success": True})
        except Exception as e:
            self._send_error(str(e))

    # === CSV endpoints ===

    def _csv_load(self, backend: MCATBackend, body: dict):
        """Load CSV file and return columns."""
        path = body.get("path")
        if not path:
            self._send_error("Missing path")
            return

        try:
            import pandas as pd
            df = pd.read_csv(path)
            row_count = len(df)

            self._send_json({
                "columns": list(df.columns),
                "row_count": row_count
            })
        except Exception as e:
            self._send_error(f"Failed to load CSV: {e}")

    def _detect_url_column(self, backend: MCATBackend, body: dict):
        """Detect URL column from column names."""
        columns = body.get("columns", [])

        # Common URL column names
        url_patterns = ["url", "link", "post_url", "video_url", "content_url", "href"]
        candidates = []
        recommended = None

        for col in columns:
            col_lower = col.lower()
            for pattern in url_patterns:
                if pattern in col_lower:
                    candidates.append(col)
                    if pattern == "url" or col_lower == pattern:
                        recommended = col
                    break

        if not recommended and candidates:
            recommended = candidates[0]

        self._send_json({
            "candidates": candidates,
            "recommended": recommended
        })

    # === Import endpoints ===

    def _import_preview(self, backend: MCATBackend, body: dict):
        """Preview import from CSV."""
        if not backend.current_project:
            self._send_error("No project open")
            return

        csv_path = body.get("csv_path")
        if not csv_path:
            self._send_error("Missing csv_path")
            return

        try:
            result = backend.project_service.preview_url_import(
                backend.current_project,
                Path(csv_path)
            )

            if result.has_error:
                self._send_error(result.error_message)
                return

            # Store for confirm
            backend._pending_import = result

            self._send_json({
                "total_in_file": result.total_in_file,
                "new_urls": result.new_urls,
                "duplicates_skipped": result.duplicates_skipped,
                "sample_urls": [row.get(backend.current_project.url_column, "") for row in result.rows_to_add[:10]] if result.rows_to_add else []
            })
        except Exception as e:
            self._send_error(f"Failed to preview import: {e}")

    def _import_confirm(self, backend: MCATBackend, body: dict):
        """Confirm and execute import."""
        if not backend.current_project:
            self._send_error("No project open")
            return

        if not hasattr(backend, '_pending_import') or not backend._pending_import:
            self._send_error("No pending import")
            return

        try:
            added = backend.project_service.confirm_url_import(
                backend.current_project,
                backend._pending_import
            )
            backend._pending_import = None
            self._send_json({"added": added})
        except Exception as e:
            self._send_error(f"Failed to import: {e}")

    # === Results endpoints ===

    def _results_combined(self, backend: MCATBackend):
        """Get combined results with status counts."""
        if not backend.current_project:
            self._send_json({
                "results": [],
                "by_status": {"live": 0, "removed": 0, "restricted": 0, "error": 0, "pending": 0}
            })
            return

        try:
            import pandas as pd
            from datetime import datetime

            results = []
            status_counts = {"live": 0, "removed": 0, "restricted": 0, "error": 0, "pending": 0}

            # Check if results file exists
            results_path = backend.current_project.combined_csv_path
            if results_path.exists():
                df = pd.read_csv(results_path)

                for _, row in df.iterrows():
                    status = str(row.get("status", "pending")).lower()
                    if status not in status_counts:
                        status = "error"

                    status_counts[status] += 1
                    results.append({
                        "url": row.get(backend.current_project.url_column, ""),
                        "status": status,
                        "info": row.get("info", ""),
                        "timestamp": row.get("timestamp", datetime.now().isoformat()),
                        "error_message": row.get("error_message")
                    })

            self._send_json({
                "results": results,
                "by_status": status_counts
            })
        except Exception as e:
            self._send_json({
                "results": [],
                "by_status": {"live": 0, "removed": 0, "restricted": 0, "error": 0, "pending": 0}
            })

    # === Logs endpoint ===

    def _get_logs(self, backend: MCATBackend):
        """Get processing logs."""
        logs = []

        # Get logs from processing service if available
        if backend.processing_service and hasattr(backend.processing_service, 'get_logs'):
            try:
                logs = backend.processing_service.get_logs()
            except:
                pass

        self._send_json({"logs": logs})

    def log_message(self, format, *args):
        """Log to stdout for Tauri to capture."""
        print(f"[API] {args[0]}", flush=True)


def main():
    port = find_available_port(DEFAULT_PORT, MAX_PORT_ATTEMPTS)
    print(f"Starting MCAT backend on port {port}...", flush=True)

    # Write port to file so Tauri can discover it
    port_file = Path(__file__).parent.parent / ".port"
    port_file.write_text(str(port))

    server = HTTPServer(("127.0.0.1", port), MCATHandler)
    print(f"Backend ready at http://127.0.0.1:{port}", flush=True)
    print("Endpoints:", flush=True)
    print("  GET  /health", flush=True)
    print("  GET  /project/status", flush=True)
    print("  POST /project/create", flush=True)
    print("  POST /project/open", flush=True)
    print("  GET  /process/status", flush=True)
    print("  POST /process/start|pause|resume|cancel", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Backend shutting down...", flush=True)
        port_file.unlink(missing_ok=True)
        server.shutdown()


if __name__ == "__main__":
    main()
