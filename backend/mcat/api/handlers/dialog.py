"""Dialog handlers — native file/folder pickers and open-external.

On Linux, uses zenity which routes through xdg-desktop-portal,
giving native dialogs on any desktop (KDE, GNOME, etc.).
On macOS/Windows, uses osascript/powershell respectively.
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path


# --- Linux (portal via zenity) ---

def _pick_file_zenity(filters: list[dict] | None = None) -> str | None:
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


def _pick_folder_zenity() -> str | None:
    result = subprocess.run(
        ["zenity", "--file-selection", "--directory"],
        capture_output=True, text=True,
    )
    return result.stdout.strip() or None


# --- macOS ---

def _pick_file_macos(filters: list[dict] | None = None) -> str | None:
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


def _pick_folder_macos() -> str | None:
    result = subprocess.run(
        ["osascript", "-e", 'POSIX path of (choose folder)'],
        capture_output=True, text=True,
    )
    return result.stdout.strip() or None


# --- Dispatch ---

def _pick_file(filters: list[dict] | None = None) -> str | None:
    system = platform.system()
    if system == "Darwin":
        return _pick_file_macos(filters)
    # Linux (and fallback)
    if shutil.which("zenity"):
        return _pick_file_zenity(filters)
    return None


def _pick_folder() -> str | None:
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
    from api.context import app_context
    target = body.get("url", "")
    if not target:
        return {"success": False}

    # Only allow HTTP(S) URLs or paths within the current project
    is_url = target.startswith("http://") or target.startswith("https://")
    is_project_path = False
    if app_context.current_project:
        try:
            resolved = Path(target).resolve()
            project_dir = app_context.current_project.project_path.resolve()
            is_project_path = str(resolved).startswith(str(project_dir))
        except Exception:
            pass

    if not is_url and not is_project_path:
        return {"success": False, "error": "Path not allowed"}

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", target])
        elif system == "Windows":
            os.startfile(target)
        else:
            subprocess.Popen(["xdg-open", target])
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
