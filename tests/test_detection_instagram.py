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
    (dict(body_text="x", title="Sorry, this isn't available"), "Unavailable"),
    (dict(body_text="x", selectors={ERROR_SVG: FakeEl()}), "Unavailable"),
    (dict(body_text="post isn't available"), "Unavailable"),
    # positive
    (dict(body_text="x", selectors={OG: FakeEl({"content": "Jane on Instagram: a photo"})}), "Live"),
    (dict(body_text="x", selectors={ARTICLE: FakeEl()}), "Live"),
    # RTL caption puts a U+200E bidi mark before the colon; the visible post's
    # login modal must not override the og:title Live signal.
    (dict(body_text="log in sign up never miss a post",
          selectors={OG: FakeEl({"content": "PPP on Instagram‎: احتجاج"})}), "Live"),
    # login wall: soft modal text, and the hard redirect to /accounts/login/
    # (whose body says "create new account", not "sign up")
    (dict(body_text="please log in or sign up to continue"), "Login Required"),
    (dict(body_text="log into instagram create new account",
          href="https://www.instagram.com/accounts/login/?next=%2Ftv%2Fx%2F"), "Login Required"),
    # no signal
    (dict(body_text="just a normal page"), None),
    # precedence: a "gone" notice beats a live og:title
    (dict(body_text="post isn't available",
          selectors={OG: FakeEl({"content": "Jane on Instagram: x"})}), "Unavailable"),
])
async def test_instagram_detection(kw, expected):
    result = await _scraper()._detect_status(FakeTab(**kw), "")
    if expected is None:
        assert result is None
    else:
        assert result is not None and result[0] == expected
