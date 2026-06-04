"""Phase 2 verification: FB parity through the REAL ported classes
(BrowserSession + FacebookScraper.check_url_status harness), plus a direct
check of the element .attrs API used by the og:title fallback.

  backend/venv/bin/python tests/experiments/zd_phase2_verify.py
"""
import asyncio
import csv
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.browser_manager import BrowserSession  # noqa: E402
from scrapers.facebook_scraper import FacebookScraper  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "fixtures/live/verified/facebook_verified_urls.csv"


async def main():
    rows = [r for r in csv.DictReader(DATA.open()) if r.get("url")]
    session = await BrowserSession.create(pool_size=3, headless=True)
    scraper = FacebookScraper(session)
    try:
        # Full harness, concurrent — exercises tab pool, rate limiter, poll loop.
        results = await asyncio.gather(*(scraper.check_url_status(r["url"]) for r in rows))
        correct = 0
        for row, res in zip(rows, results):
            ok = res.status == row["status"]
            correct += ok
            print(f"expected={row['status']:8} got={res.status:8} {'OK ' if ok else 'MISS'} "
                  f"info={res.info[:28]:28} {row['url']}")
        print(f"\nParity (real harness): {correct}/{len(rows)}")

        # Directly exercise the .attrs path (og:title) on a known-live post.
        live = next(r["url"] for r in rows if r["status"] == "Live")
        tab = await session.acquire_tab()
        await tab.get(live)
        await tab.sleep(4)
        meta = await tab.query_selector('meta[property="og:title"]')
        content = meta.attrs.get("content") if meta else None
        await session.release_tab(tab)
        print(f"\nog:title .attrs check: {'PASS' if content else 'FAIL'} -> {str(content)[:60]!r}")
    finally:
        await session.stop()


if __name__ == "__main__":
    asyncio.run(main())
