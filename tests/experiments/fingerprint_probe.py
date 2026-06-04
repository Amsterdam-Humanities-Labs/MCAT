"""Compare bot-detection fingerprint signals across Chrome option sets.

Runs the same JS probe under each configuration so we can decide — with data,
not guesses — whether switching to --headless=new and dropping --disable-gpu
actually improves the automation/headless tells before touching driver_manager.

Reuses the app's real base options + OS-correct UA, varying only the two knobs
under test (headless mode, --disable-gpu).

  backend/venv/bin/python tests/experiments/fingerprint_probe.py

Caveat: the WebGL renderer depends on the *host* GPU. On a GPU-less box every
config may report software rendering (SwiftShader); the GPU benefit of dropping
--disable-gpu is best confirmed on the researcher's actual laptop. The webdriver
flag and UA/client-hint consistency checks are host-independent.
"""
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

import chromedriver_autoinstaller  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402

from core.driver_manager import (  # noqa: E402
    resolve_chromedriver_path,
    base_chrome_options,
    os_user_agent,
)

FP_JS = r"""
const gl = (() => {
  try {
    const c = document.createElement('canvas');
    const g = c.getContext('webgl') || c.getContext('experimental-webgl');
    if (!g) return {vendor: null, renderer: null};
    const ext = g.getExtension('WEBGL_debug_renderer_info');
    return {
      vendor: ext ? g.getParameter(ext.UNMASKED_VENDOR_WEBGL) : g.getParameter(g.VENDOR),
      renderer: ext ? g.getParameter(ext.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER),
    };
  } catch (e) { return {vendor: 'err', renderer: String(e)}; }
})();
const d = navigator.userAgentData || null;
return {
  webdriver: navigator.webdriver,
  userAgent: navigator.userAgent,
  platform: navigator.platform,
  uaDataPlatform: d ? d.platform : null,
  uaDataMobile: d ? d.mobile : null,
  languages: (navigator.languages || []).join(','),
  hardwareConcurrency: navigator.hardwareConcurrency,
  webglVendor: gl.vendor,
  webglRenderer: gl.renderer,
};
"""

# (label, headless-arg or None, disable_gpu)
CONFIGS = [
    ("current   --headless + --disable-gpu", "--headless", True),
    ("new-hl    --headless=new + --disable-gpu", "--headless=new", True),
    ("new+gpu   --headless=new, no --disable-gpu", "--headless=new", False),
    ("headed    (no headless) [needs a display]", None, False),
]


def make_options(headless_arg, disable_gpu):
    opts = base_chrome_options()
    if headless_arg:
        opts.add_argument(headless_arg)
    if disable_gpu:
        opts.add_argument("--disable-gpu")
    major = (chromedriver_autoinstaller.get_chrome_version() or "124.0").split(".")[0]
    opts.add_argument(f"--user-agent={os_user_agent(major)}")
    return opts


def probe(headless_arg, disable_gpu):
    driver = webdriver.Chrome(
        service=Service(resolve_chromedriver_path()),
        options=make_options(headless_arg, disable_gpu),
    )
    try:
        driver.set_page_load_timeout(30)
        driver.get("https://example.com")  # real https origin so userAgentData populates
        return driver.execute_script(FP_JS)
    finally:
        driver.quit()


KEYS = [
    "webdriver", "platform", "uaDataPlatform",
    "webglVendor", "webglRenderer", "userAgent",
]


def main():
    for label, hl, gpu in CONFIGS:
        print(f"\n=== {label} ===")
        try:
            r = probe(hl, gpu)
            for k in KEYS:
                print(f"  {k:16}: {r.get(k)}")
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {str(e)[:160]}")


if __name__ == "__main__":
    main()
