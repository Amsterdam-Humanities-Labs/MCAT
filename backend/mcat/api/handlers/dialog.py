"""Dialog handlers — native file/folder pickers and open-external.

On Linux, uses zenity which routes through xdg-desktop-portal,
giving native dialogs on any desktop (KDE, GNOME, etc.).
On macOS/Windows, uses osascript/powershell respectively.
"""

import platform
import shutil
import subprocess


# --- Linux (portal via zenity) ---

def _pick_file_zenity(filters=None):
    cmd = ["zenity", "--file-selection"]
    if filters:
        for f in filters:
            exts = " ".join(f"*.{e}" for e in f.get("extensions", []))
            name = f.get("name", "Files")
            cmd.extend(["--file-filter", f"{name} | {exts}"])
    # Always add an "All files" option
    cmd.extend(["--file-filter", "All files | *"])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() or None


def _pick_folder_zenity():
    result = subprocess.run(
        ["zenity", "--file-selection", "--directory"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() or None


# --- macOS ---

def _pick_file_macos(filters=None):
    ext_list = []
    if filters:
        for f in filters:
            ext_list.extend(f.get("extensions", []))
    type_clause = ""
    if ext_list:
        types = ", ".join(f'"{e}"' for e in ext_list)
        type_clause = f" of type {{{types}}}"
    script = f'POSIX path of (choose file{type_clause})'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return result.stdout.strip() or None


def _pick_folder_macos():
    result = subprocess.run(
        ["osascript", "-e", 'POSIX path of (choose folder)'],
        capture_output=True, text=True,
    )
    return result.stdout.strip() or None


# --- Dispatch ---

def _pick_file(filters=None):
    system = platform.system()
    if system == "Darwin":
        return _pick_file_macos(filters)
    # Linux (and fallback)
    if shutil.which("zenity"):
        return _pick_file_zenity(filters)
    return None


def _pick_folder():
    system = platform.system()
    if system == "Darwin":
        return _pick_folder_macos()
    if shutil.which("zenity"):
        return _pick_folder_zenity()
    return None


def open_file(body: dict) -> dict:
    """Open a file picker dialog."""
    path = _pick_file(body.get("filters"))
    return {"path": path}


def open_folder(body: dict) -> dict:
    """Open a folder picker dialog."""
    path = _pick_folder()
    return {"path": path}


def open_external(body: dict) -> dict:
    """Open a file or URL in the system default application."""
    target = body.get("url", "")
    if not target:
        return {"success": False}

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", target])
        elif system == "Windows":
            subprocess.Popen(["start", "", target], shell=True)
        else:
            subprocess.Popen(["xdg-open", target])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
