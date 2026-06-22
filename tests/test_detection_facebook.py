"""Detection branch coverage for FacebookScraper._detect_status (offline, FakeTab)."""
import pytest

from scrapers.facebook_scraper import FacebookScraper
from _fakes import FakeTab, FakeEl

OG = 'meta[property="og:title"]'
ARTICLE = 'div[role="article"]'


def _scraper():
    return FacebookScraper(None)


@pytest.mark.parametrize("kw, expected", [
    # negative
    (dict(body_text="this content isn't available"), "Removed"),
    (dict(body_text="the link you followed may be broken"), "Removed"),
    # positive
    (dict(body_text="x", selectors={ARTICLE: FakeEl()}), "Live"),
    (dict(body_text="x", selectors={OG: FakeEl({"content": "A real post headline"})}), "Live"),
    (dict(body_text="x", title="A real post | Facebook"), "Live"),
    # generic-title guards must NOT be read as Live
    (dict(body_text="x", selectors={OG: FakeEl({"content": "Facebook"})}), None),
    (dict(body_text="x", title="Log in to Facebook | Facebook"), None),
    # login-walled / undecided -> Unknown (no login-required branch by design)
    (dict(body_text="you must log in to continue", title="Facebook"), None),
    # precedence: removal beats the rendered article
    (dict(body_text="this content isn't available", selectors={ARTICLE: FakeEl()}), "Removed"),
])
async def test_facebook_detection(kw, expected):
    result = await _scraper()._detect_status(FakeTab(**kw), "")
    if expected is None:
        assert result is None
    else:
        assert result is not None and result[0] == expected
