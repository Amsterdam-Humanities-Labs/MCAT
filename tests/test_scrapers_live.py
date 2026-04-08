"""
Live scraper integration tests.

Runs scrapers against real URLs to verify detection strategies.
Requires a filled-in CSV at tests/fixtures/scraper_test_urls.csv

Usage:
    cd pywebview-app/backend
    python -m pytest ../../tests/test_scrapers_live.py -v
    python -m pytest ../../tests/test_scrapers_live.py -v -k facebook
    python -m pytest ../../tests/test_scrapers_live.py -v -k youtube
    python -m pytest ../../tests/test_scrapers_live.py -v -k instagram
    python -m pytest ../../tests/test_scrapers_live.py -v -k twitter
"""

import csv
import sys
import pytest
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "pywebview-app" / "backend" / "mcat"
sys.path.insert(0, str(backend_dir))

from core.driver_manager import WebDriverPool
from scrapers.youtube_scraper import YouTubeScraper
from scrapers.instagram_scraper import InstagramScraper
from scrapers.facebook_scraper import FacebookScraper
from scrapers.twitter_scraper import TwitterScraper

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "scraper_test_urls.csv"

SCRAPERS = {
    "youtube": YouTubeScraper,
    "instagram": InstagramScraper,
    "facebook": FacebookScraper,
    "twitter": TwitterScraper,
}


def load_test_urls():
    """Load test URLs from CSV, skipping rows with empty URLs."""
    rows = []
    with open(FIXTURES_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if row["url"].strip():
                rows.append(row)
    return rows


def get_platform_urls(platform):
    """Get test URLs for a specific platform."""
    return [r for r in load_test_urls() if r["platform"] == platform]


# Shared driver pool — created once per test session
@pytest.fixture(scope="session")
def driver_pool():
    pool = WebDriverPool(pool_size=2, headless=True)
    yield pool
    pool.cleanup()


@pytest.fixture(scope="session")
def youtube_scraper(driver_pool):
    return YouTubeScraper(driver_pool)


@pytest.fixture(scope="session")
def instagram_scraper(driver_pool):
    return InstagramScraper(driver_pool)


@pytest.fixture(scope="session")
def facebook_scraper(driver_pool):
    return FacebookScraper(driver_pool)


@pytest.fixture(scope="session")
def twitter_scraper(driver_pool):
    return TwitterScraper(driver_pool)


def make_test_id(row):
    """Create readable test ID from row."""
    url = row["url"]
    # Truncate URL for display
    short = url[:60] + "..." if len(url) > 60 else url
    return f"{row['expected_status']}: {short}"


# --- YouTube ---

youtube_urls = get_platform_urls("youtube") if FIXTURES_PATH.exists() else []


@pytest.mark.skipif(not youtube_urls, reason="No YouTube test URLs in fixture CSV")
@pytest.mark.parametrize("row", youtube_urls, ids=[make_test_id(r) for r in youtube_urls])
def test_youtube(youtube_scraper, row):
    result = youtube_scraper.check_url_status(row["url"])
    assert result.status == row["expected_status"], (
        f"\n  URL:      {row['url']}"
        f"\n  Expected: {row['expected_status']}"
        f"\n  Got:      {result.status}"
        f"\n  Info:     {result.info}"
        f"\n  Error:    {result.error_message}"
    )


# --- Instagram ---

instagram_urls = get_platform_urls("instagram") if FIXTURES_PATH.exists() else []


@pytest.mark.skipif(not instagram_urls, reason="No Instagram test URLs in fixture CSV")
@pytest.mark.parametrize("row", instagram_urls, ids=[make_test_id(r) for r in instagram_urls])
def test_instagram(instagram_scraper, row):
    result = instagram_scraper.check_url_status(row["url"])
    assert result.status == row["expected_status"], (
        f"\n  URL:      {row['url']}"
        f"\n  Expected: {row['expected_status']}"
        f"\n  Got:      {result.status}"
        f"\n  Info:     {result.info}"
        f"\n  Error:    {result.error_message}"
    )


# --- Facebook ---

facebook_urls = get_platform_urls("facebook") if FIXTURES_PATH.exists() else []


@pytest.mark.skipif(not facebook_urls, reason="No Facebook test URLs in fixture CSV")
@pytest.mark.parametrize("row", facebook_urls, ids=[make_test_id(r) for r in facebook_urls])
def test_facebook(facebook_scraper, row):
    result = facebook_scraper.check_url_status(row["url"])
    assert result.status == row["expected_status"], (
        f"\n  URL:      {row['url']}"
        f"\n  Expected: {row['expected_status']}"
        f"\n  Got:      {result.status}"
        f"\n  Info:     {result.info}"
        f"\n  Error:    {result.error_message}"
    )


# --- Twitter ---

twitter_urls = get_platform_urls("twitter") if FIXTURES_PATH.exists() else []


@pytest.mark.skipif(not twitter_urls, reason="No Twitter test URLs in fixture CSV")
@pytest.mark.parametrize("row", twitter_urls, ids=[make_test_id(r) for r in twitter_urls])
def test_twitter(twitter_scraper, row):
    result = twitter_scraper.check_url_status(row["url"])
    assert result.status == row["expected_status"], (
        f"\n  URL:      {row['url']}"
        f"\n  Expected: {row['expected_status']}"
        f"\n  Got:      {result.status}"
        f"\n  Info:     {result.info}"
        f"\n  Error:    {result.error_message}"
    )
