### install
```pip install -r requirements.txt```

### dev
```python src/main.py```

## Building

### Self-building on Linux/macOS

**Prerequisites:**
- Python 3.11+
- On Linux: install `patchelf`
  - Ubuntu/Debian: `apt install patchelf`
  - Fedora/RHEL: `dnf install patchelf`

**Build command:**
```bash
pip install nuitka
nuitka --standalone --onefile --enable-plugin=no-qt --output-dir=dist src/main.py
```

The built executable will be in the `dist/` folder.

### Automated builds
GitHub Actions automatically builds for macOS and Fedora on every push to main branch.

