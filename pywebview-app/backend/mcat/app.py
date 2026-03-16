"""
MCAT Desktop App — pywebview entry point.

Starts the Python backend server, then opens a native webview window.
In dev mode (no dist/ build), also spawns the Vite dev server automatically.
"""

import os
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


def start_vite():
    """Spawn the Vite dev server and return the process."""
    print(f"Starting Vite dev server on port {VITE_PORT}...", flush=True)
    proc = subprocess.Popen(
        ["pnpm", "vite", "--port", str(VITE_PORT)],
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if not wait_for_port(VITE_PORT, timeout=15.0):
        print("Warning: Vite dev server may not have started", flush=True)
    else:
        print(f"Vite dev server ready at http://127.0.0.1:{VITE_PORT}", flush=True)
    return proc


def main():
    port = find_available_port(DEFAULT_PORT, MAX_PORT_ATTEMPTS)
    print(f"Starting MCAT backend on port {port}...", flush=True)

    port_file = Path(__file__).parent.parent / ".port"
    port_file.write_text(str(port))

    # Start backend in background thread
    backend_thread = threading.Thread(target=start_backend, args=(port,), daemon=True)
    backend_thread.start()
    wait_for_port(port)

    # Determine mode: dev (no build) or production (dist/ exists)
    vite_proc = None
    is_dev = not (DIST_DIR / "index.html").exists()

    if is_dev:
        vite_proc = start_vite()
        frontend_url = f"http://127.0.0.1:{VITE_PORT}?port={port}"
    else:
        frontend_url = str(DIST_DIR / "index.html") + f"?port={port}"

    try:
        import webview
        window = webview.create_window(
            "MCAT",
            frontend_url,
            width=1200,
            height=800,
            min_size=(800, 600),
        )
        webview.start()
    except ImportError:
        url = f"http://127.0.0.1:{VITE_PORT if is_dev else port}?port={port}"
        print(f"pywebview not installed. Open {url} in your browser.", flush=True)
        print("Install with: pip install pywebview", flush=True)
        try:
            backend_thread.join()
        except KeyboardInterrupt:
            pass
    finally:
        if vite_proc:
            vite_proc.terminate()
            vite_proc.wait()
        port_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
