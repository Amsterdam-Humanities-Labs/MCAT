"""Detection branch coverage for InstagramScraper._detect_status (offline, FakeTab)."""
import pytest

from scrapers.instagram_scraper import InstagramScraper
from _fakes import FakeTab, FakeEl

OG = 'meta[property="og:title"]'
ERROR_SVG = 'svg[aria-label="error"]'
ARTICLE = 'article[role="presentation"]'


def _scraper():
    return InstagramScraper(None)


@pytest.mark.parametrize("kw, expected", [
    # negative
    (dict(body_text="x", title="Sorry, this isn't available"), "Removed"),
    (dict(body_text="x", selectors={ERROR_SVG: FakeEl()}), "Removed"),
    (dict(body_text="post isn't available"), "Removed"),
    # positive
    (dict(body_text="x", selectors={OG: FakeEl({"content": "Jane on Instagram: a photo"})}), "Live"),
    (dict(body_text="x", selectors={ARTICLE: FakeEl()}), "Live"),
    # login wall
    (dict(body_text="please log in or sign up to continue"), "Login Required"),
    # no signal
    (dict(body_text="just a normal page"), None),
    # precedence: removal beats a live og:title
    (dict(body_text="post isn't available",
          selectors={OG: FakeEl({"content": "Jane on Instagram: x"})}), "Removed"),
])
async def test_instagram_detection(kw, expected):
    result = await _scraper()._detect_status(FakeTab(**kw), "")
    if expected is None:
        assert result is None
    else:
        assert result is not None and result[0] == expected
