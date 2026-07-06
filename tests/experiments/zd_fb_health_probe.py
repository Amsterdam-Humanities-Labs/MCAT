"""Why do FB tabs go unresponsive after one page? Measure evaluate('1') (the
health probe) at each stage of a real FB post load, then test recovery.

For each URL, on one reused tab:
  health on blank -> get() -> health -> innerText -> health -> screenshot ->
  health -> get(about:blank) -> health -> 2nd get(url) -> health

Reading:
  - eval TIMEOUT on the live page but 'ok' after about:blank, and 2nd get works
    -> health check is a FALSE POSITIVE (tab held by FB's page) -> fix = reset to
       about:blank between URLs instead of full recycle.
  - eval THREW / about:blank fails / 2nd get fails -> tab genuinely dead -> recycle
       is legitimately needed.

Run: backend/venv/bin/python tests/experiments/zd_fb_health_probe.py
"""
import asyncio
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "mcat"))

import zendriver as zd
from core.browser_manager import BROWSER_ARGS, resolved_user_agent

HEALTH_TIMEOUT = 5.0   # matches BrowserSession.HEALTH_CHECK_TIMEOUT
URLS = [
    "https://www.facebook.com/timcastnews/posts/3762011610552718",
    "https://www.facebook.com/GuardianUs/posts/4234429359917432",
    "https://www.facebook.com/TheHill/posts/10159033718074087",
]


async def timed(coro, timeout):
    t0 = time.time()
    try:
        v = await asyncio.wait_for(coro, timeout=timeout)
        return "ok", v, time.time() - t0
    except asyncio.TimeoutError:
        return "TIMEOUT", None, time.time() - t0
    except Exception as e:
        return "THREW", e.__class__.__name__, time.time() - t0


async def health(tab):
    s, v, dt = await timed(tab.evaluate("1"), HEALTH_TIMEOUT)
    return f"{s} in {dt:.1f}s"


async def probe(browser, url, shot_dir):
    print(f"\n=== {url}")
    tab = await browser.get("about:blank", new_tab=True)
    print(f"  health on blank         : {await health(tab)}")

    s, v, dt = await timed(tab.get(url), 30)
    print(f"  get(url)                : {s} in {dt:.1f}s")
    print(f"  health after load       : {await health(tab)}")

    s, v, dt = await timed(tab.evaluate("document.body.innerText"), 10)
    print(f"  body.innerText          : {('len=' + str(len(v))) if s == 'ok' and v else s} in {dt:.1f}s")
    print(f"  health after innerText  : {await health(tab)}")

    s, v, dt = await timed(tab.save_screenshot(f"{shot_dir}/probe.jpg"), 15)
    print(f"  screenshot              : {s}{'' if s == 'ok' else ' ' + str(v)} in {dt:.1f}s")
    print(f"  health after screenshot : {await health(tab)}")

    s, v, dt = await timed(tab.get("about:blank"), 15)
    print(f"  get(about:blank)        : {s} in {dt:.1f}s")
    print(f"  health after blank reset: {await health(tab)}")

    s, v, dt = await timed(tab.get(url), 30)
    print(f"  2nd get(url) same tab   : {s} in {dt:.1f}s")
    print(f"  health after 2nd get    : {await health(tab)}")

    try:
        await asyncio.wait_for(tab.close(), timeout=5)
    except Exception:
        pass


async def main():
    browser = await zd.start(headless=True, sandbox=False,
                             user_agent=resolved_user_agent(), browser_args=BROWSER_ARGS)
    shot = tempfile.mkdtemp()
    try:
        for url in URLS:
            try:
                await probe(browser, url, shot)
            except Exception as e:
                print(f"  PROBE ERROR: {e.__class__.__name__}: {e}")
            await asyncio.sleep(2)
    finally:
        await browser.stop()


asyncio.run(main())
