"""
PyInstaller hook for pywebview.

On Linux: collects GTK/WebKit GI typelibs needed for the GTK backend.
On macOS: only collects pywebview's JS assets (native WebKit, no GTK).
"""

import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

binaries = []
datas = collect_data_files("webview")
hiddenimports = collect_submodules("webview")

if sys.platform == "linux":
    from PyInstaller.utils.hooks.gi import get_gi_typelibs

    def _add_gi(namespace: str, version: str) -> bool:
        try:
            b, d, h = get_gi_typelibs(namespace, version)
            binaries.extend(b)
            datas.extend(d)
            hiddenimports.extend(h)
            return True
        except ValueError:
            return False

    if not _add_gi("WebKit2", "4.1"):
        _add_gi("WebKit2", "4.0")

    if not _add_gi("Soup", "3.0"):
        _add_gi("Soup", "2.4")

    if not _add_gi("JavaScriptCore", "4.1"):
        _add_gi("JavaScriptCore", "4.0")
