"""PyInstaller hook for zendriver.

zendriver's `cdp` submodules are imported dynamically (generated from the Chrome
DevTools Protocol), so PyInstaller's static analysis misses them. Collect every
submodule and any bundled data so the packaged app can drive Chrome.
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules("zendriver")
datas = collect_data_files("zendriver")
