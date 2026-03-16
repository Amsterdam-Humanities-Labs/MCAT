# MCAT Tauri

Desktop app with Tauri (Rust) + Svelte frontend + Python backend.

## Prerequisites

- Node.js 20.19+ or 22.12+
- pnpm
- Rust (cargo)
- Python 3.10+ (via pyenv)
- Tauri system deps (`webkit2gtk`, `libsoup3` on Linux)

## Setup

```bash
# Install Python 3.10
cd backend && pyenv install 3.10 && pyenv local 3.10 && cd ..

# Install all dependencies
pnpm install
cd backend && python -m venv .venv && .venv/bin/pip install -e .
```

## Development

```bash
pnpm dev              # Full app (Tauri + UI + Python backend)
pnpm dev:frontend     # UI only (localhost:5180)
pnpm dev:backend      # Python backend only
```

## Build

```bash
pnpm build            # Build release app
```

## Project Structure

```
tauri-prototype/
├── frontend/          # Svelte UI
├── tauri/             # Rust/Tauri shell
└── backend/           # Python backend
    ├── .venv/         # Virtual environment
    └── mcat/          # Backend code
        └── server.py  # HTTP server
```

## Troubleshooting

### Linux/Wayland: Window decorations missing or GTK errors

On Wayland (especially KDE Plasma), you may see errors like:
```
Gdk-CRITICAL: gdk_wayland_window_get_wl_surface: assertion failed
Gdk-Message: Error 22 (Invalid argument) dispatching to Wayland display
```

The app uses X11 fallback by default (`GDK_BACKEND=x11` in dev script). If you removed this, add it back:

```bash
GDK_BACKEND=x11 pnpm dev
```

This also fixes missing window decorations (minimize/maximize/close buttons).
