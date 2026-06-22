"""Probe what an X (twitter) tweet URL exposes when LOGGED OUT, via zendriver.

Goal: decide whether an X account is required and which detection signals survive
without one (redirect-to-login? server-rendered og: meta? rendered tweet article?).

Run: backend/venv/bin/python tests/experiments/zd_twitter_probe.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "mcat"))

import zendriver as zd
from core.browser_manager import BROWSER_ARGS, resolved_user_agent

URLS = [
    ("sample", "https://x.com/AJCGlobal/status/1471179832696442882"),
    ("sample", "https://x.com/jwaonline/status/1468370751980032001"),
    ("sample", "https://x.com/PuppetJared/status/1436807769185832965"),
    ("nonexistent-id", "https://x.com/jack/status/1"),
]


async def meta(tab, prop):
    el = await tab.query_selector(f'meta[property="{prop}"]')
    return el.attrs.get("content") if el else None


async def probe(tab, url):
    try:
        await asyncio.wait_for(tab.get(url), timeout=25)
    except Exception as e:
        return {"load_error": str(e)}
    await asyncio.sleep(4)  # let the SPA settle / any redirect happen
    body = (await tab.evaluate("document.body.innerText") or "")
    low = body.lower()
    return {
        "final_url": await tab.evaluate("location.href"),
        "title": await tab.evaluate("document.title"),
        "og:title": await meta(tab, "og:title"),
        "og:description": (await meta(tab, "og:description") or "")[:90],
        "tweet_article": bool(await tab.query_selector('article[data-testid="tweet"]')),
        "login_signal": any(s in low for s in
                            ["log in to x", "sign in to x", "to see more", "don’t miss",
                             "don't miss", "see what’s happening", "see what's happening"]),
        "gone_signal": any(s in low for s in
                           ["doesn’t exist", "doesn't exist", "this post is unavailable",
                            "account suspended", "this account doesn", "post unavailable",
                            "something went wrong", "hmm...this page"]),
        "body_len": len(body),
        "body_snip": body[:140].replace("\n", " "),
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
            print(f"  {k:15}: {v}")
    await browser.stop()


asyncio.run(main())
