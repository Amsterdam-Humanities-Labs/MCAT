# MCAT Tauri

Desktop app with Tauri (Rust) + Svelte frontend + Python backend.

## Prerequisites

- Node.js 20+
- pnpm
- Rust (cargo)
- Python 3.10 (via pyenv)
- Tauri system deps (`webkit2gtk`, `libsoup3` on Linux)

## Setup

```bash
# Install Python 3.10
cd backend && pyenv install 3.10 && pyenv local 3.10 && cd ..

# Install all dependencies
pnpm install:all
```

## Development

```bash
pnpm dev              # Full app (Tauri + UI + Python backend)
pnpm dev:ui           # UI only (localhost:5180)
pnpm dev:backend      # Python backend only
```

## Build

```bash
pnpm build            # Build release app
pnpm bundle:backend   # Bundle Python with PyInstaller
```

## Project Structure

```
apps/desktop/      # Tauri/Rust shell
packages/ui/       # Svelte frontend
backend/           # Python backend
  .venv/           # Virtual environment
  mcat/server.py   # HTTP server
```
