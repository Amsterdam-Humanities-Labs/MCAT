"""Decisive anti-detection comparison: our REAL production Selenium config
(WebDriverPool, headless=new, OS UA, no --disable-gpu, stealth flags) vs
zendriver, both against bot.sannysoft — which probes CDP/automation tells the
surface JS probe can't see. Prints per-signal pass/fail side by side.

  backend/venv/bin/python tests/experiments/bot_detection_compare.py
"""
import asyncio
import sys
import time
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

import zendriver as zd  # noqa: E402
from core.driver_manager import WebDriverPool  # noqa: E402

URL = "https://bot.sannysoft.com"

# IIFE expression (works as a zendriver evaluate expression and, with "return "
# prefixed, as a Selenium execute_script body).
EXTRACT = r"""(function(){
  var out=[];
  document.querySelectorAll('table tr').forEach(function(tr){
    var c=tr.querySelectorAll('td');
    if(c.length>=2){
      var r=c[1];
      out.push({
        name:(c[0].innerText||'').trim().slice(0,38),
        val:(r.innerText||'').replace(/\s+/g,' ').trim().slice(0,30),
        bg:getComputedStyle(r).backgroundColor
      });
    }
  });
  return out;
})()"""


def verdict(bg):
    """bot.sannysoft colors result cells green=pass / red=fail."""
    try:
        nums = [int(x) for x in bg.replace("rgb(", "").replace(")", "").split(",")[:3]]
        r, g, b = nums
    except Exception:
        return "?"
    if g > r + 20:
        return "PASS"
    if r > g + 20:
        return "FAIL"
    return "-"


def collect_selenium():
    pool = WebDriverPool(pool_size=1, headless=True)
    d = pool.get_driver()
    try:
        d.get(URL)
        time.sleep(6)
        return d.execute_script("return " + EXTRACT)
    finally:
        pool.return_driver(d)
        pool.cleanup()


async def collect_zendriver():
    browser = await zd.start(headless=True)
    try:
        tab = await browser.get(URL)
        await tab.sleep(6)
        return await tab.evaluate(EXTRACT)
    finally:
        await browser.stop()


def main():
    print("collecting Selenium (production config)...")
    sel = {row["name"]: row for row in collect_selenium()}
    print("collecting zendriver...")
    zen = {row["name"]: row for row in asyncio.run(collect_zendriver())}

    names = list(dict.fromkeys(list(sel) + list(zen)))
    sel_p = sel_f = zen_p = zen_f = 0
    print(f"\n{'signal':40} {'selenium':>22} {'zendriver':>22}")
    print("-" * 88)
    for n in names:
        s, z = sel.get(n), zen.get(n)
        sv = verdict(s["bg"]) if s else "—"
        zv = verdict(z["bg"]) if z else "—"
        sel_p += sv == "PASS"; sel_f += sv == "FAIL"
        zen_p += zv == "PASS"; zen_f += zv == "FAIL"
        flag = "  <-- differs" if sv != zv and "-" not in (sv, zv) and "—" not in (sv, zv) else ""
        sval = (s["val"] if s else "")[:14]
        zval = (z["val"] if z else "")[:14]
        print(f"{n[:40]:40} {sv:>5} {sval:<15} {zv:>5} {zval:<15}{flag}")
    print("-" * 88)
    print(f"{'TOTALS':40} {f'{sel_p}P/{sel_f}F':>22} {f'{zen_p}P/{zen_f}F':>22}")


if __name__ == "__main__":
    main()
