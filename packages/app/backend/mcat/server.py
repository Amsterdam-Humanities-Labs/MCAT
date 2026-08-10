"""
MCAT Backend Server for Tauri.

Lean HTTP server entry point. Business logic is in api/handlers/.
"""

import http.client
import json
import mimetypes
import secrets
import socket
import sys
import threading
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Ensure mcat directory is in path for imports
mcat_dir = Path(__file__).parent
if str(mcat_dir) not in sys.path:
    sys.path.insert(0, str(mcat_dir))

from api.router import GET_ROUTES, POST_ROUTES
from events import event_bus

DEFAULT_PORT = 9876
MAX_PORT_ATTEMPTS = 10

AUTH_HEADER = "X-MCAT-Token"


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

    # In production this is set to the built frontend dir so the SPA is served
    # from the same origin as the API. It stays None in dev, where Vite serves
    # the SPA over http and only the API hits this server.
    static_dir: "Path | None" = None

    # Exact origins allowed to read API responses, and the hosts this server
    # answers to. Both are populated by app.py once the port is known.
    allowed_origins: "set[str]" = set()
    allowed_hosts: "set[str]" = set()

    # Minted at startup and handed to the SPA in its URL. Without it a page in
    # the user's ordinary browser could POST here, since the routes take no auth.
    auth_token: str = ""

    def _cors_origin(self) -> "str | None":
        """The request's Origin if it is one we allow, else None (send no header)."""
        origin = self.headers.get("Origin", "")
        return origin if origin in self.allowed_origins else None

    def _apply_cors(self) -> None:
        origin = self._cors_origin()
        if origin is not None:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def _host_allowed(self) -> bool:
        """Guards DNS rebinding: a rebound page is same-origin, so CORS never runs."""
        if not self.allowed_hosts:
            return True
        return self.headers.get("Host", "") in self.allowed_hosts

    def _token_ok(self, query_token: "str | None" = None) -> bool:
        """Token from the header, or the query string for EventSource, which
        cannot set headers."""
        if not self.auth_token:
            return True
        supplied = query_token if query_token is not None else self.headers.get(AUTH_HEADER, "")
        return secrets.compare_digest(supplied or "", self.auth_token)

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._apply_cors()
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
        """Handle CORS preflight. Never token-gated: a preflight cannot carry
        custom headers, so gating it would reject every POST before it starts."""
        if not self._host_allowed():
            self.send_response(421)
            self.end_headers()
            return
        self.send_response(200)
        self._apply_cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", f"Content-Type, {AUTH_HEADER}")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        if not self._host_allowed():
            self._send_error("Host not allowed", 421)
            return

        parsed = urlparse(self.path)
        path = parsed.path

        # SSE endpoint
        if path == "/events":
            token = parse_qs(parsed.query).get("token", [""])[0]
            if not self._token_ok(token):
                self._send_error("Forbidden", 403)
                return
            self._handle_sse()
            return

        routes = GET_ROUTES

        handler = routes.get(path)
        if handler:
            # API routes are gated; static below is not, since the SPA's own
            # page and asset requests carry no token.
            if not self._token_ok():
                self._send_error("Forbidden", 403)
                return
            try:
                result = handler(self.path)
                self._send_json(result)
            except Exception as e:
                print(f"[ERROR] GET {path}: {e}", flush=True)
                self._send_error(str(e))
        elif self.static_dir is not None:
            self._serve_static(path)
        else:
            self._send_error("Not found", 404)

    def _serve_static(self, path: str) -> None:
        """Serve the built SPA from static_dir (same origin as the API). Loading
        the UI from here instead of file:// is what lets it fetch the backend:
        macOS WKWebView blocks a file:// page from reaching http://127.0.0.1.
        Unknown paths fall back to index.html so the SPA can route them."""
        assert self.static_dir is not None
        root = self.static_dir.resolve()
        target = (root / (path.lstrip("/") or "index.html")).resolve()
        if not target.is_relative_to(root):
            self._send_error("Forbidden", 403)
            return
        if not target.is_file():
            target = root / "index.html"
            if not target.is_file():
                self._send_error("Not found", 404)
                return
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_sse(self):
        """Handle Server-Sent Events connection."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._apply_cors()
        self.end_headers()

        # Subscribe to events
        queue = event_bus.subscribe()

        try:
            while True:
                # Get event with timeout for heartbeat
                event = event_bus.get_event(queue, timeout=15.0)
                if event is None:
                    # Send heartbeat comment to keep connection alive
                    self.wfile.write(b": heartbeat\n\n")
                else:
                    # Send event
                    event_type = event.get("type", "message")
                    data = json.dumps(event)
                    self.wfile.write(f"event: {event_type}\ndata: {data}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            # Client disconnected
            pass
        finally:
            event_bus.unsubscribe(queue)

    def do_POST(self):
        """Handle POST requests."""
        if not self._host_allowed():
            self._send_error("Host not allowed", 421)
            return
        if not self._token_ok():
            self._send_error("Forbidden", 403)
            return
        # A non-JSON content type is what lets a page POST here without a
        # preflight, so require the exact type the SPA sends.
        content_type = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            self._send_error("Unsupported Media Type", 415)
            return

        path = urlparse(self.path).path
        routes = POST_ROUTES

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
                # Log successful responses for key endpoints
                if path.startswith("/project/") or path.startswith("/process/") or path.startswith("/run/") or path.startswith("/tracking/"):
                    print(f"[OK] POST {path} → {json.dumps(result)[:200]}", flush=True)
            except ValueError as e:
                print(f"[ERROR] POST {path}: {e}", flush=True)
                self._send_error(str(e))
            except Exception as e:
                import traceback
                print(f"[ERROR] POST {path}: {e}", flush=True)
                traceback.print_exc()
                self._send_error(str(e), 500)
        else:
            self._send_error("Not found", 404)

    def log_message(self, format, *args):
        """Log to stdout, suppressing routine polling requests.

        Keep /events suppressed: it is the one request carrying the auth token in
        its query string (EventSource cannot set headers), so logging it would
        print the token to stdout.
        """
        message = args[0] if args else ""
        # Suppress frequent polling endpoints and SSE from API logs
        if any(ep in message for ep in ["/health", "/project/status", "/events"]):
            return
        print(f"[API] {message}", flush=True)


