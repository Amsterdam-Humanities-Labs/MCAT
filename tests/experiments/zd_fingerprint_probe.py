"""zendriver fingerprint, to compare against the Selenium baseline.

Selenium baseline (after our fixes): webdriver=False, UA/platform consistent,
WebGL present (SwiftShader). The question for the spike: does zendriver give an
equal-or-cleaner fingerprint NATIVELY — and is navigator.webdriver gone without
us hand-rolling stealth flags?

  backend/venv/bin/python tests/experiments/zd_fingerprint_probe.py
"""
import asyncio
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

import zendriver as zd  # noqa: E402
from core.driver_manager import resolved_user_agent  # noqa: E402

FP_JS = r"""
(() => {
  const gl = (() => {
    try {
      const c = document.createElement('canvas');
      const g = c.getContext('webgl') || c.getContext('experimental-webgl');
      if (!g) return {vendor: null, renderer: null};
      const e = g.getExtension('WEBGL_debug_renderer_info');
      return {
        vendor: e ? g.getParameter(e.UNMASKED_VENDOR_WEBGL) : g.getParameter(g.VENDOR),
        renderer: e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER),
      };
    } catch (e) { return {vendor: 'err', renderer: String(e)}; }
  })();
  const d = navigator.userAgentData || null;
  return {
    webdriver: navigator.webdriver,
    userAgent: navigator.userAgent,
    platform: navigator.platform,
    uaDataPlatform: d ? d.platform : null,
    webglVendor: gl.vendor,
    webglRenderer: gl.renderer,
  };
})()
"""

KEYS = ["webdriver", "platform", "uaDataPlatform", "webglVendor", "webglRenderer", "userAgent"]


async def probe(label, **start_kwargs):
    print(f"\n=== {label} ===")
    try:
        browser = await zd.start(headless=True, **start_kwargs)
    except Exception as e:
        print(f"  LAUNCH ERROR: {type(e).__name__}: {str(e)[:160]}")
        return
    try:
        tab = await browser.get("https://example.com")
        await tab.sleep(1)
        r = await tab.evaluate(FP_JS)
        for k in KEYS:
            print(f"  {k:16}: {r.get(k)}")
    except Exception as e:
        print(f"  PROBE ERROR: {type(e).__name__}: {str(e)[:160]}")
    finally:
        await browser.stop()


async def main():
    await probe("zendriver default (headless)")
    await probe("zendriver + OS-correct UA", user_agent=resolved_user_agent())


if __name__ == "__main__":
    asyncio.run(main())
