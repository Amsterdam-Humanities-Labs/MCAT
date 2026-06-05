# PyInstaller spec for MCAT.
#
# Cross-platform: produces onedir bundle on Linux, .app bundle on macOS.
#
# Run from the backend/ directory:
#     python -m PyInstaller --clean mcat.spec

# pyright: reportMissingImports=false
# ruff: noqa
import sys
from pathlib import Path

SPEC_DIR = Path(SPECPATH)
PROJECT_ROOT = SPEC_DIR.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

if not FRONTEND_DIST.exists():
    raise SystemExit(
        f"Frontend build not found at {FRONTEND_DIST}. "
        "Run `pnpm --filter frontend build` first."
    )


a = Analysis(
    ["mcat/app.py"],
    pathex=[str(SPEC_DIR / "mcat")],
    binaries=[],
    datas=[(str(FRONTEND_DIST), "frontend/dist")],
    hiddenimports=[],
    hookspath=[str(SPEC_DIR / "hooks")],
    excludes=[
        "PyQt5", "PyQt6", "PySide2", "PySide6", "tkinter",
        "unittest", "test", "tests",
        "xmlrpc",
        "pydoc", "doctest", "argparse",
        "ftplib", "imaplib", "smtplib", "poplib", "nntplib", "telnetlib",
        "turtle", "turtledemo",
        "idlelib", "lib2to3",
        "distutils", "setuptools", "pip", "pkg_resources",
        "multiprocessing",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mcat",
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    upx_exclude=[],
    name="mcat",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="MCAT.app",
        icon=None,
        bundle_identifier="com.mcat.app",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "0.1.0",
        },
    )
