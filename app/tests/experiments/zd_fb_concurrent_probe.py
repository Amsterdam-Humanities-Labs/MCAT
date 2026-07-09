"""Reproduce the run's condition: 3 concurrent tabs, sustained, each REUSED
without recycling, pulling real FB URLs. Per URL log load time + health probe
(evaluate('1'), 5s). On a health failure, test whether get(about:blank) recovers
the tab.

Answers: does a reused tab degrade under concurrent+sustained FB load, at what
point, and does about:blank recover it (reset suffices) or not (genuine death)?

Run: backend/venv/bin/python tests/experiments/zd_fb_concurrent_probe.py
"""
import asyncio
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "mcat"))

import zendriver as zd
from core.browser_manager import BROWSER_ARGS, resolved_user_agent

N = 60
POOL = 3
FIX = str(Path(__file__).parent.parent / "fixtures" / "live" / "unverified"
          / "facebook_sample_stopthesteal_2020.csv")


def urls():
    with open(FIX, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return [row["url"] for _, row in zip(range(N), r) if row.get("url")]


async def timed(coro, timeout):
    t0 = time.time()
    try:
        await asyncio.wait_for(coro, timeout=timeout)
        return "ok", time.time() - t0
    except asyncio.TimeoutError:
        return "TIMEOUT", time.time() - t0
    except Exception as e:
        return f"THREW:{e.__class__.__name__}", time.time() - t0


async def worker(wid, browser, queue, results):
    tab = await browser.get("about:blank", new_tab=True)
    while True:
        try:
            idx, url = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        ls, ld = await timed(tab.get(url), 30)
        hs, hd = await timed(tab.evaluate("1"), 5)
        recov = ""
        if hs != "ok":
            rs, rd = await timed(tab.get("about:blank"), 10)
            rh, rhd = await timed(tab.evaluate("1"), 5)
            recov = f"  >> blank_reset: get={rs}({rd:.1f}s) health={rh}({rhd:.1f}s)"
        print(f"[w{wid}] #{idx:2d} load={ls}({ld:4.1f}s) health={hs}({hd:.1f}s){recov}", flush=True)
        results.append(hs == "ok")


async def main():
    browser = await zd.start(headless=True, sandbox=False,
                             user_agent=resolved_user_agent(), browser_args=BROWSER_ARGS)
    q = asyncio.Queue()
    for i, u in enumerate(urls()):
        q.put_nowait((i, u))
    results = []
    try:
        await asyncio.gather(*(worker(w, browser, q, results) for w in range(POOL)))
    finally:
        ok = sum(results)
        print(f"\nhealthy_after_load = {ok}/{len(results)}")
        await browser.stop()


asyncio.run(main())
