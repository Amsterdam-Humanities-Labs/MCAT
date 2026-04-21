#!/bin/bash
# Build MCAT for Linux.
#
# Output: build/MCAT-x86_64.AppImage — single double-clickable file.
#
# Pipeline:
#   1. Build the Svelte frontend → frontend/dist/
#   2. Run PyInstaller → backend/dist/mcat/ (onedir bundle)
#   3. Assemble an AppDir (staging folder with standard layout)
#   4. Package the AppDir with appimagetool → .AppImage

set -euo pipefail

# Resolve paths relative to this script, not the caller's cwd
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# -- Prerequisites -----------------------------------------------------------

command -v pnpm >/dev/null || { echo "pnpm not found"; exit 1; }
[[ -x "${ROOT}/backend/venv/bin/python" ]] \
    || { echo "backend venv not found — run: cd backend && python3 -m venv --system-site-packages venv"; exit 1; }
"${ROOT}/backend/venv/bin/python" -c "import PyInstaller" 2>/dev/null \
    || { echo "PyInstaller not importable in venv — run: backend/venv/bin/pip install pyinstaller"; exit 1; }

APPIMAGETOOL="${SCRIPT_DIR}/appimagetool-x86_64.AppImage"
if [[ ! -x "${APPIMAGETOOL}" ]]; then
    echo "Downloading appimagetool..."
    curl -L -o "${APPIMAGETOOL}" \
        https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "${APPIMAGETOOL}"
fi

# -- 1. Build frontend -------------------------------------------------------

echo ">> Building frontend"
cd "${ROOT}"
pnpm --filter frontend build

# -- 2. Run PyInstaller ------------------------------------------------------

echo ">> Running PyInstaller"
cd "${ROOT}/backend"
rm -rf build dist
venv/bin/python -m PyInstaller --clean mcat.spec

# -- 3. Assemble AppDir ------------------------------------------------------

echo ">> Assembling AppDir"
APPDIR="${SCRIPT_DIR}/MCAT.AppDir"
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"

# Copy the onedir bundle's contents into usr/bin
cp -r "${ROOT}/backend/dist/mcat/." "${APPDIR}/usr/bin/"

# Bundle license texts so they ship with the app
mkdir -p "${APPDIR}/usr/share"
cp "${ROOT}/LICENSE" "${APPDIR}/usr/share/LICENSE"
cp -r "${ROOT}/LICENSES" "${APPDIR}/usr/share/"

# Metadata files required at the AppDir root
cp "${SCRIPT_DIR}/AppRun" "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun"
cp "${SCRIPT_DIR}/mcat.desktop" "${APPDIR}/mcat.desktop"

# Icon — use a placeholder if none supplied. AppImages require an icon at
# the AppDir root named matching the desktop file's Icon= field.
if [[ -f "${SCRIPT_DIR}/mcat.png" ]]; then
    cp "${SCRIPT_DIR}/mcat.png" "${APPDIR}/mcat.png"
else
    echo "   (no build/mcat.png found, using 1x1 transparent placeholder)"
    printf '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82' > "${APPDIR}/mcat.png"
fi

# -- 4. Package AppImage -----------------------------------------------------

echo ">> Packaging AppImage"
cd "${SCRIPT_DIR}"
ARCH=x86_64 "${APPIMAGETOOL}" "${APPDIR}" "${SCRIPT_DIR}/MCAT-x86_64.AppImage"

echo
echo "Built: ${SCRIPT_DIR}/MCAT-x86_64.AppImage"
echo "Run it with: ${SCRIPT_DIR}/MCAT-x86_64.AppImage"
