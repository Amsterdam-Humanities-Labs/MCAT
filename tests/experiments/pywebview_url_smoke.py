"""
pywebview URL smoke test — companion to pywebview_smoke.py.

pywebview_smoke.py (inline HTML) is interactive on this Mac, and the MCAT page
is interactive in Chrome, yet the MCAT window in pywebview is completely inert.
The remaining variable is pywebview loading a *URL* (vs inline HTML), which is
what this isolates: it loads a plain external page the same way MCAT loads its
frontend (URL + text_select=True), with NO backend thread and NO MCAT code.

Run it with the same venv Python as the app:

    backend/venv/bin/python tests/experiments/pywebview_url_smoke.py
    # optionally point it at any URL (e.g. MCAT's dev URL while `pnpm dev` runs):
    backend/venv/bin/python tests/experiments/pywebview_url_smoke.py http://127.0.0.1:5180?port=9876

How to read the result (try clicking the "More information..." link and
selecting text on example.com):
  * Interactive  ->  loading a URL is fine; the freeze is specific to the MCAT
    page in WKWebView (look next at the SSE connection, the pywebview JS bridge
    injection, or something the SPA does that wedges the content process).
  * Dead (no clicks/selection)  ->  loading any URL (vs inline HTML) wedges this
    pywebview build — a narrow pywebview version/config bug; try pinning an
    older pywebview (e.g. 5.4).

debug=True enables the Web Inspector (right-click -> Inspect Element).
"""

import platform
import sys

import webview

url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"

print(f"python    : {sys.version.split()[0]}  base_prefix={sys.base_prefix}")
print(f"pywebview : {getattr(webview, '__version__', 'unknown')}")
print(f"macOS     : {platform.mac_ver()[0]}  arch={platform.machine()}")
print(f"loading   : {url}")

webview.create_window("pywebview url smoke test", url, text_select=True)
webview.start(debug=True)
