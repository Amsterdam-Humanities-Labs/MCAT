"""Phase 3 verification: IG / YT verified-set parity through the real ported
scraper harness (anonymous).

  backend/venv/bin/python tests/experiments/zd_phase3_verify.py [instagram] [youtube]
"""
import asyncio
import csv
import sys
from pathlib import Path

BACKEND_MCAT = Path(__file__).resolve().parents[2] / "backend" / "mcat"
sys.path.insert(0, str(BACKEND_MCAT))

from core.browser_manager import BrowserSession  # noqa: E402
from scrapers.instagram_scraper import InstagramScraper  # noqa: E402
from scrapers.youtube_scraper import YouTubeScraper  # noqa: E402

FIX = Path(__file__).resolve().parents[1] / "fixtures/live/verified"
SCRAPERS = {
    "instagram": (InstagramScraper, FIX / "instagram_verified_urls.csv"),
    "youtube": (YouTubeScraper, FIX / "youtube_verified_urls.csv"),
}


async def run(platform, pool=3):
    cls, path = SCRAPERS[platform]
    rows = [r for r in csv.DictReader(path.open()) if r.get("url")]
    session = await BrowserSession.create(pool_size=pool, headless=True)
    scraper = cls(session)
    try:
        results = await asyncio.gather(*(scraper.check_url_status(r["url"]) for r in rows))
        correct = sum(res.status == row["status"] for row, res in zip(rows, results))
        print(f"\n=== {platform}: {correct}/{len(rows)} ===")
        for row, res in zip(rows, results):
            ok = res.status == row["status"]
            print(f"  exp={row['status']:13} got={res.status:13} {'OK ' if ok else 'MISS'} {row['url']}")
    finally:
        await session.stop()


async def main():
    for p in (sys.argv[1:] or ["instagram", "youtube"]):
        await run(p)


if __name__ == "__main__":
    asyncio.run(main())
