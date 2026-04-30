"""
Live scraper integration tests.

Runs scrapers against verified URLs in tests/fixtures/live/verified/.
Each CSV uses the standard format: platform,url,title,status

Usage:
    cd backend
    python -m pytest ../tests/test_scrapers_live.py -v
    python -m pytest ../tests/test_scrapers_live.py -v -k youtube
    python -m pytest ../tests/test_scrapers_live.py -v -k facebook
    python -m pytest ../tests/test_scrapers_live.py -v -k instagram
    python -m pytest ../tests/test_scrapers_live.py -v -k twitter
"""

import csv
import sys
import pytest
from pathlib import Path

backend_dir = Path(__file__).parent.parent / "backend" / "mcat"
sys.path.insert(0, str(backend_dir))

from core.driver_manager import WebDriverPool
from scrapers.youtube_scraper import YouTubeScraper
from scrapers.instagram_scraper import InstagramScraper
from scrapers.facebook_scraper import FacebookScraper
from scrapers.twitter_scraper import TwitterScraper

VERIFIED_DIR = Path(__file__).parent / "fixtures" / "live" / "verified"


def load_verified_urls(platform):
    """Load verified URLs for a platform from all CSVs in the verified directory."""
    rows = []
    if not VERIFIED_DIR.exists():
        return rows
    for csv_path in VERIFIED_DIR.glob("*.csv"):
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row.get("platform") == platform and row.get("url", "").strip() and row.get("status", "").strip():
                    rows.append(row)
    return rows


def make_test_id(row):
    title = row.get("title", "")[:40]
    return f"{row['status']}: {title}" if title else f"{row['status']}: {row['url'][:50]}"


# Shared driver pool
@pytest.fixture(scope="session")
def driver_pool():
    pool = WebDriverPool(pool_size=2, headless=True)
    yield pool
    pool.cleanup()


def _init_scraper(cls, driver_pool):
    scraper = cls(driver_pool)
    scraper.cancel_event = None
    return scraper


@pytest.fixture(scope="session")
def youtube_scraper(driver_pool):
    return _init_scraper(YouTubeScraper, driver_pool)


@pytest.fixture(scope="session")
def instagram_scraper(driver_pool):
    return _init_scraper(InstagramScraper, driver_pool)


@pytest.fixture(scope="session")
def facebook_scraper(driver_pool):
    return _init_scraper(FacebookScraper, driver_pool)


@pytest.fixture(scope="session")
def twitter_scraper(driver_pool):
    return _init_scraper(TwitterScraper, driver_pool)


# --- YouTube ---

youtube_urls = load_verified_urls("youtube")


@pytest.mark.skipif(not youtube_urls, reason="No verified YouTube URLs")
@pytest.mark.parametrize("row", youtube_urls, ids=[make_test_id(r) for r in youtube_urls])
def test_youtube(youtube_scraper, row):
    result = youtube_scraper.check_url_status(row["url"])
    assert result.status == row["status"], (
        f"\n  URL:      {row['url']}"
        f"\n  Expected: {row['status']}"
        f"\n  Got:      {result.status}"
        f"\n  Info:     {result.info}"
        f"\n  Error:    {result.error_message}"
    )


# --- Instagram ---

instagram_urls = load_verified_urls("instagram")


@pytest.mark.skipif(not instagram_urls, reason="No verified Instagram URLs")
@pytest.mark.parametrize("row", instagram_urls, ids=[make_test_id(r) for r in instagram_urls])
def test_instagram(instagram_scraper, row):
    result = instagram_scraper.check_url_status(row["url"])
    assert result.status == row["status"], (
        f"\n  URL:      {row['url']}"
        f"\n  Expected: {row['status']}"
        f"\n  Got:      {result.status}"
        f"\n  Info:     {result.info}"
        f"\n  Error:    {result.error_message}"
    )


# --- Facebook ---

facebook_urls = load_verified_urls("facebook")


@pytest.mark.skipif(not facebook_urls, reason="No verified Facebook URLs")
@pytest.mark.parametrize("row", facebook_urls, ids=[make_test_id(r) for r in facebook_urls])
def test_facebook(facebook_scraper, row):
    result = facebook_scraper.check_url_status(row["url"])
    assert result.status == row["status"], (
        f"\n  URL:      {row['url']}"
        f"\n  Expected: {row['status']}"
        f"\n  Got:      {result.status}"
        f"\n  Info:     {result.info}"
        f"\n  Error:    {result.error_message}"
    )


# --- Twitter ---

twitter_urls = load_verified_urls("twitter")


@pytest.mark.skipif(not twitter_urls, reason="No verified Twitter URLs")
@pytest.mark.parametrize("row", twitter_urls, ids=[make_test_id(r) for r in twitter_urls])
def test_twitter(twitter_scraper, row):
    result = twitter_scraper.check_url_status(row["url"])
    assert result.status == row["status"], (
        f"\n  URL:      {row['url']}"
        f"\n  Expected: {row['status']}"
        f"\n  Got:      {result.status}"
        f"\n  Info:     {result.info}"
        f"\n  Error:    {result.error_message}"
    )
