"""
Minimal pywebview smoke test — isolates pywebview/WKWebView from the MCAT app.

Why this exists: the MCAT window renders but is completely inert on macOS (no
hover, no clicks; resize / Cmd-Tab / clicking the header tab do nothing), while
the pywebview debug log shows the Cocoa renderer and NO errors. This script
loads a bare HTML button with NO backend, NO Vite and NO MCAT code, so it answers
one question: is pywebview itself interactive on this machine?

Run it with the SAME venv Python used for the app:

    cd backend && venv/bin/python ../tests/experiments/pywebview_smoke.py
    # or from the repo root:
    backend/venv/bin/python tests/experiments/pywebview_smoke.py

How to read the result:
  * Button turns red on hover AND shows "CLICKED" on click, and the mousemove
    line updates  ->  pywebview works; the bug is MCAT-specific (how app.py
    creates the window, the backend thread, or the dev URL). Debug MCAT next.
  * Button is dead (no hover, no click, mousemove never updates)  ->  pywebview/
    WKWebView itself is not interactive on this machine, independent of MCAT.
    Next step is environment-level: try a different pywebview version (e.g. 5.4)
    or a different Python, not changes to MCAT.

debug=True enables the Web Inspector (right-click -> Inspect Element): if the
inspector opens but the page still won't hover, events aren't reaching the web
content at all (a responder/process issue) rather than a paint issue.
"""

import platform
import sys

import webview

print(f"python    : {sys.version.split()[0]}  base_prefix={sys.base_prefix}")
print(f"pywebview : {getattr(webview, '__version__', 'unknown')}")
print(f"macOS     : {platform.mac_ver()[0]}  arch={platform.machine()}")

HTML = """
<!doctype html>
<html>
  <body style="font-family: system-ui; padding: 40px;">
    <button
      style="font-size: 24px; padding: 30px;"
      onmouseover="this.style.background='red'"
      onmouseout="this.style.background=''"
      onclick="this.textContent='CLICKED'"
    >hover + click me</button>
    <p id="moved">mousemove: none yet</p>
    <script>
      document.addEventListener('mousemove', (e) => {
        document.getElementById('moved').textContent =
          'mousemove: ' + e.clientX + ',' + e.clientY;
      });
    </script>
  </body>
</html>
"""

webview.create_window("pywebview smoke test", html=HTML)
webview.start(debug=True)
