"""
MCAT Backend Server for Tauri.

Lean HTTP server entry point. Business logic is in api/handlers/.
"""

import json
import socket
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Ensure mcat directory is in path for imports
mcat_dir = Path(__file__).parent
if str(mcat_dir) not in sys.path:
    sys.path.insert(0, str(mcat_dir))

from api.router import get_routes, post_routes

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
        routes = get_routes()

        handler = routes.get(path)
        if handler:
            try:
                result = handler(self.path)
                self._send_json(result)
            except Exception as e:
                self._send_error(str(e))
        else:
            self._send_error("Not found", 404)

    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path
        routes = post_routes()

        try:
            body = self._read_json_body()
        except json.JSONDecodeError:
            self._send_error("Invalid JSON")
            return

        handler = routes.get(path)
        if handler:
            try:
                result = handler(body)
                self._send_json(result)
            except ValueError as e:
                self._send_error(str(e))
            except Exception as e:
                self._send_error(str(e), 500)
        else:
            self._send_error("Not found", 404)

    def log_message(self, format, *args):
        """Log to stdout, suppressing routine polling requests."""
        message = args[0] if args else ""
        if "/health" in message or "/project/status" in message or "/process/status" in message:
            return
        print(f"[API] {message}", flush=True)


def main():
    port = find_available_port(DEFAULT_PORT, MAX_PORT_ATTEMPTS)
    print(f"Starting MCAT backend on port {port}...", flush=True)

    port_file = Path(__file__).parent.parent / ".port"
    port_file.write_text(str(port))

    server = HTTPServer(("127.0.0.1", port), MCATHandler)
    print(f"Backend ready at http://127.0.0.1:{port}", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Backend shutting down...", flush=True)
        port_file.unlink(missing_ok=True)
        server.shutdown()


if __name__ == "__main__":
    main()
