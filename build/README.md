# Linux Build

Produces `MCAT-x86_64.AppImage` — a single double-clickable file that runs on any glibc-compatible Linux distro.

## Quick start

```bash
pnpm build:linux
```

or directly:

```bash
./build/build-linux.sh
```

Output lands at `build/MCAT-x86_64.AppImage`.

## How it works

The build pipeline has four steps, each isolated for debuggability:

1. **Frontend build** — `pnpm --filter frontend build` → `frontend/dist/`
2. **PyInstaller** — reads `backend/mcat.spec`, produces `backend/dist/mcat/` (onedir bundle: executable + Python libs + bundled frontend)
3. **AppDir assembly** — copies the bundle into `build/MCAT.AppDir/` with the standard AppImage layout (`AppRun`, `*.desktop`, `*.png`, `usr/bin/`)
4. **AppImage packaging** — runs `appimagetool` on the AppDir to produce the final `.AppImage`

## Files in this directory

| File | Purpose |
|------|---------|
| `build-linux.sh` | Orchestrates all 4 steps above. Idempotent — safe to re-run. |
| `AppRun` | Shell script that AppImages execute when launched. Invokes `usr/bin/mcat`. |
| `mcat.desktop` | App metadata (name, icon, categories). Read by file managers and the AppImage runtime. |
| `mcat.png` | App icon (256x256 PNG). Falls back to 1x1 placeholder if missing. |
| `appimagetool-x86_64.AppImage` | Downloaded on first run. Gitignored. |
| `MCAT.AppDir/` | Staging folder built by the script. Gitignored. |
| `MCAT-x86_64.AppImage` | Final artifact. Gitignored. |

## Related files outside this directory

- `backend/mcat.spec` — PyInstaller config (what to include, what to exclude, entry point)
- `backend/hooks/hook-webview.py` — PyInstaller hook collecting pywebview's GTK/WebKit dependencies
- `backend/mcat/app.py` — has a `sys.frozen` branch that swaps `FRONTEND_DIR` to point at the bundled location at runtime

## Troubleshooting

### "QT cannot be loaded" when running the AppImage

The WebKit typelibs weren't collected. Check `backend/hooks/hook-webview.py` — it tries WebKit2 4.1 first, then 4.0. If your distro ships a different version, add a case there.

### "chromedriver not found" at runtime

Expected — `chromedriver_autoinstaller` downloads chromedriver into the user's cache directory (`~/.local/lib/python*/site-packages/chromedriver_autoinstaller/`) on first use, not at build time. A fresh first run needs network access.

### Binary is much larger than expected

Check `backend/mcat.spec`'s `excludes=` list. PyInstaller pulls in Qt/tkinter by default when pywebview is present, adding ~200MB. The current excludes should prevent that — if size explodes, verify the list is still correct.

### "Frontend build not found" when running PyInstaller

You're running `pyinstaller` directly without building the frontend first. Use `./build-linux.sh` instead, or run `pnpm --filter frontend build` manually before invoking pyinstaller.
