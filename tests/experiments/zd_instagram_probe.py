"""Probe what an Instagram post URL exposes LOGGED OUT, via zendriver, to see
why a visible post (behind the "Never miss a post from XYZ" soft modal) is being
tagged Login Required.

Run: backend/venv/bin/python tests/experiments/zd_instagram_probe.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "mcat"))

import zendriver as zd
from core.browser_manager import BROWSER_ARGS, resolved_user_agent
from scrapers.instagram_scraper import InstagramScraper

URLS = [
    ("tv, genuine login gate -> Unknown?", "https://www.instagram.com/tv/CH3sscogC3P/"),
    ("reported (looks visible)", "https://www.instagram.com/p/CHqVy3-A2o9/"),
    ("known-live fixture", "https://www.instagram.com/p/CH9GrAbn7fE/"),
]


async def meta(tab, prop):
    el = await tab.query_selector(f'meta[property="{prop}"]')
    return el.attrs.get("content") if el else None


async def probe(tab, url):
    try:
        await asyncio.wait_for(tab.get(url), timeout=25)
    except Exception as e:
        return {"load_error": str(e)}
    await asyncio.sleep(5)  # let the SPA settle
    body = (await tab.evaluate("document.body.innerText") or "")
    low = body.lower()
    og_title = await meta(tab, "og:title")
    detected = await InstagramScraper(None)._detect_status(tab, "")
    return {
        "final_url": await tab.evaluate("location.href"),
        "title": await tab.evaluate("document.title"),
        "og:title": og_title,
        "og:type": await meta(tab, "og:type"),
        "og:image?": bool(await meta(tab, "og:image")),
        "' on Instagram:' (scraper check)": bool(og_title and " on Instagram:" in og_title),
        "' on Instagram' (loose)": bool(og_title and " on Instagram" in og_title),
        "article[role=presentation]?": bool(await tab.query_selector('article[role="presentation"]')),
        "any <article>?": bool(await tab.query_selector('article')),
        "post <img>?": bool(await tab.query_selector('article img, main img')),
        "'log in'+'sign up'?": ("log in" in low and "sign up" in low),
        "'never miss a post'?": ("never miss a post" in low),
        "SCRAPER VERDICT": detected,
        "body_len": len(body),
        "body_snip": body[:160].replace("\n", " "),
    }


async def main():
    browser = await zd.start(
        headless=True, sandbox=False,
        user_agent=resolved_user_agent(), browser_args=BROWSER_ARGS,
    )
    tab = browser.main_tab
    for label, url in URLS:
        print(f"\n=== [{label}] {url}")
        for k, v in (await probe(tab, url)).items():
            print(f"  {k:34}: {v}")
    await browser.stop()


asyncio.run(main())
