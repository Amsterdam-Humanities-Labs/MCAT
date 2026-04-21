"""
PyInstaller hook for pywebview on Linux.

pywebview's GTK backend depends on GObject Introspection (gi) bindings for
WebKit, Soup, and JavaScriptCore. PyInstaller doesn't auto-detect these —
they're loaded dynamically via typelibs at runtime. Without this hook,
the frozen app raises "QT cannot be loaded" or "You must have either QT or GTK".

We collect:
  - Binaries: the .so libraries (libwebkit2gtk, libsoup, libjavascriptcorejit)
  - Data: the .typelib files that gi reads to know what's available
  - Hidden imports: gi.repository.WebKit2, Soup, JavaScriptCore

If WebKit 4.1 typelibs are missing, try 4.0 — older distros ship only 4.0.
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from PyInstaller.utils.hooks.gi import get_gi_typelibs

binaries = []
# pywebview ships a `js/` directory of JavaScript files it injects into the
# rendered page at runtime. `collect_data_files` walks the package and includes
# non-.py files (the JS assets, CSS, etc.) so they're available in the bundle.
datas = collect_data_files("webview")
hiddenimports = collect_submodules("webview")


def _add_gi(namespace: str, version: str) -> bool:
    """Collect a gi typelib, return True if found."""
    try:
        b, d, h = get_gi_typelibs(namespace, version)
        binaries.extend(b)
        datas.extend(d)
        hiddenimports.extend(h)
        return True
    except ValueError:
        return False


# WebKit2 — try 4.1 first (Ubuntu 22.04+, Fedora 36+), fall back to 4.0
if not _add_gi("WebKit2", "4.1"):
    _add_gi("WebKit2", "4.0")

# Soup — 3.0 on newer distros, 2.4 on older
if not _add_gi("Soup", "3.0"):
    _add_gi("Soup", "2.4")

# JavaScriptCore — matches the WebKit2 version above
if not _add_gi("JavaScriptCore", "4.1"):
    _add_gi("JavaScriptCore", "4.0")
