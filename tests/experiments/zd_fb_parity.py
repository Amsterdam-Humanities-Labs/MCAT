"""FB detection parity: the current facebook_scraper._detect_status logic,
ported to zendriver (async), run anonymously against the verified fixture and
compared to ground-truth labels. Proves the detection survives the CDP port.

  backend/venv/bin/python tests/experiments/zd_fb_parity.py
"""
import asyncio
import csv
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

import zendriver as zd  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "fixtures/live/verified/facebook_verified_urls.csv"
SHOTS = Path(__file__).resolve().parent / "shots" / "zd_fb_parity"
SHOTS.mkdir(parents=True, exist_ok=True)

# Copied verbatim from facebook_scraper so the logic under test is identical.
REMOVAL_PHRASES = (
    "this content isn't available",
    "this page isn't available",
    "content isn't available right now",
    "sorry, this content isn't available",
    "the link you followed may be broken",
    "page not found",
    "this content has been removed",
)
GENERIC_TITLES = {"facebook", "log in to facebook", "log into facebook"}


async def detect_status(tab):
    """Mirror of facebook_scraper._detect_status, async/zendriver."""
    try:
        page_text = (await tab.evaluate("document.body.innerText") or "").lower()
    except Exception:
        return None

    for phrase in REMOVAL_PHRASES:
        if phrase in page_text:
            return ("Removed", phrase)

    if await tab.query_selector('div[role="article"]'):
        return ("Live", "article")

    meta = await tab.query_selector('meta[property="og:title"]')
    if meta:
        content = (await meta.get_attribute("content") or "").strip()
        if content and content.lower() not in GENERIC_TITLES:
            return ("Live", "og:title")

    title = (await tab.evaluate("document.title") or "").strip().lower()
    title = title.removeprefix("(1) ").strip()
    if " | facebook" in title:
        lead = title.split(" | facebook")[0].strip()
        if lead and lead not in GENERIC_TITLES:
            return ("Live", "title")

    return None


async def main():
    rows = [r for r in csv.DictReader(DATA.open()) if r.get("url")]
    print(f"verified set: {len(rows)} urls (anonymous)\n")

    browser = await zd.start(headless=True)
    correct = 0
    try:
        for i, row in enumerate(rows):
            url, expected = row["url"], row["status"]
            try:
                tab = await browser.get(url)
                await tab.sleep(6)  # let FB's SPA render
                verdict = await detect_status(tab)
            except Exception as e:
                verdict = None
                print(f"   (error on {url}: {type(e).__name__}: {str(e)[:80]})")
            status = verdict[0] if verdict else "Unknown"
            ok = status == expected
            correct += ok
            try:
                await tab.save_screenshot(str(SHOTS / f"{i:02d}_{status}_{'OK' if ok else 'MISS'}.png"))
            except Exception:
                pass
            sig = verdict[1] if verdict else "-"
            print(f"{i:02d} expected={expected:8} got={status:8} {'OK ' if ok else 'MISS'} "
                  f"via={sig:9} {url}")
        print(f"\nParity: {correct}/{len(rows)}")
    finally:
        await browser.stop()


if __name__ == "__main__":
    asyncio.run(main())
