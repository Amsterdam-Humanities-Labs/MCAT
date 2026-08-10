"""
MCAT Desktop App — pywebview entry point.

Starts the Python backend server, then opens a native webview window.
In dev mode (no dist/ build), also spawns the Vite dev server automatically.
"""

import os
import secrets
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path

# Ensure mcat package is importable
mcat_dir = Path(__file__).parent
if str(mcat_dir) not in sys.path:
    sys.path.insert(0, str(mcat_dir))

from server import find_available_port, MCATHandler, DEFAULT_PORT, MAX_PORT_ATTEMPTS

# Resolve paths. When frozen (PyInstaller bundle), files live under sys._MEIPASS.
# In dev, walk up from backend/mcat/app.py to the project root.
if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys._MEIPASS)  # type: ignore[attr-defined]  # PyInstaller runtime
    FRONTEND_DIR = PROJECT_ROOT / "frontend"
    DIST_DIR = FRONTEND_DIR / "dist"
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    FRONTEND_DIR = PROJECT_ROOT / "frontend"
    DIST_DIR = FRONTEND_DIR / "dist"

VITE_PORT = 5180


def start_backend(port: int):
    """Start the HTTP backend server in a thread."""
    server = ThreadingHTTPServer(("127.0.0.1", port), MCATHandler)
    print(f"Backend ready at http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


def wait_for_port(port: int, timeout: float = 5.0):
    """Wait until a port is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def find_available_vite_port(start: int, attempts: int = 10) -> int:
    """Find an available port for Vite starting from the given port."""
    for i in range(attempts):
        port = start + i
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                continue  # port in use
        except OSError:
            return port
    return start + attempts


def start_vite():
    """Spawn the Vite dev server and return (process, port)."""
    vite_port = find_available_vite_port(VITE_PORT)
    print(f"Starting Vite dev server on port {vite_port}...", flush=True)
    proc = subprocess.Popen(
        ["pnpm", "vite", "--port", str(vite_port), "--strictPort", "--host", "127.0.0.1", "--clearScreen", "false"],
        cwd=str(FRONTEND_DIR),
    )
    if not wait_for_port(vite_port, timeout=15.0):
        print("Warning: Vite dev server may not have started", flush=True)
    else:
        print(f"Vite dev server ready at http://127.0.0.1:{vite_port}", flush=True)
    return proc, vite_port


WORKER_JOIN_TIMEOUT = 10.0


def shutdown_backend():
    """Stop the current run and wait briefly for its worker to unwind.

    webview.start() returns once the window closes. Without this the worker is a
    daemon, so the interpreter exits while it is mid-teardown and leaves its
    Chrome reparented and unreaped.
    """
    try:
        from api.context import app_context
        from api.handlers.auth import shutdown_login
        service = app_context.processing_service
        app_context.close_project()
        if service is not None and not service.join(timeout=WORKER_JOIN_TIMEOUT):
            print(f"Worker still running after {WORKER_JOIN_TIMEOUT:.0f}s; exiting anyway", flush=True)
        shutdown_login(timeout=WORKER_JOIN_TIMEOUT)
    except Exception as e:
        print(f"Shutdown cleanup failed: {e}", flush=True)


def main():
    port = find_available_port(DEFAULT_PORT, MAX_PORT_ATTEMPTS)
    print(f"Starting MCAT backend on port {port}...", flush=True)

    # Only this exact host:port answers, so a rebound DNS name gets a 421 rather
    # than becoming same-origin with the backend.
    MCATHandler.allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    MCATHandler.allowed_origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
    # Handed to the SPA in its URL; every API call must present it back.
    MCATHandler.auth_token = secrets.token_urlsafe(32)

    # Start backend in background thread
    backend_thread = threading.Thread(target=start_backend, args=(port,), daemon=True)
    backend_thread.start()
    wait_for_port(port)

    # Determine mode: dev (no build) or production (dist/ exists)
    vite_proc = None
    is_dev = not (DIST_DIR / "index.html").exists()

    vite_port = VITE_PORT
    token = MCATHandler.auth_token
    if is_dev:
        vite_proc, vite_port = start_vite()
        # Vite serves the SPA from its own origin, so in dev the API really is
        # cross-origin and that origin has to be allowed.
        MCATHandler.allowed_origins |= {
            f"http://127.0.0.1:{vite_port}", f"http://localhost:{vite_port}"
        }
        frontend_url = f"http://127.0.0.1:{vite_port}?port={port}&token={token}"
    else:
        # Serve the built SPA from the backend itself so the UI and API share one
        # origin (http://127.0.0.1:port). Loading it from file:// instead makes
        # macOS WKWebView block every fetch to the http backend: the UI renders
        # but all buttons/API calls silently fail.
        MCATHandler.static_dir = DIST_DIR
        frontend_url = f"http://127.0.0.1:{port}/?port={port}&token={token}"

    try:
        import webview
        window = webview.create_window(
            "MCAT",
            frontend_url,
            width=1200,
            height=800,
            min_size=(800, 600),
            text_select=True,
        )
        webview.start()
    except ImportError:
        url = f"http://127.0.0.1:{vite_port if is_dev else port}?port={port}"
        print(f"pywebview not installed. Open {url} in your browser.", flush=True)
        print("Install with: pip install pywebview", flush=True)
        try:
            backend_thread.join()
        except KeyboardInterrupt:
            pass
    finally:
        shutdown_backend()
        if vite_proc:
            vite_proc.terminate()
            vite_proc.wait()


if __name__ == "__main__":
    main()
