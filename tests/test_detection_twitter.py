"""Detection branch coverage for TwitterScraper._detect_status (offline, FakeTab)."""
import pytest

from scrapers.twitter_scraper import TwitterScraper
from _fakes import FakeTab, FakeEl

OG = 'meta[property="og:title"]'
ARTICLE = 'article[data-testid="tweet"]'


def _scraper():
    return TwitterScraper(None)


@pytest.mark.parametrize("kw, expected", [
    # positive (a rendered tweet / "on X" signal is conclusive)
    (dict(title="jane on X: hello world"), "Live"),
    (dict(selectors={OG: FakeEl({"content": "jane on X: hi"})}), "Live"),
    (dict(selectors={ARTICLE: FakeEl()}), "Live"),
    # platform takedown vs owner-gated vs gone
    (dict(body_text="This Post is from a suspended account"), "Moderated"),
    (dict(body_text="This Post is from a protected account"), "Restricted"),
    (dict(body_text="Hmm...this page doesn't exist. nothing to see here"), "Unavailable"),
    # X's real 404, curly apostrophe (matched up to the apostrophe)
    (dict(body_text="Hmm…this page doesn’t exist. Try searching for something else."), "Unavailable"),
    (dict(title="X / ?"), "Unavailable"),
    # no signal
    (dict(body_text="just some text", title="random"), None),
    # precedence: positive-first — a rendered tweet wins even if the text
    # mentions moderation (X only renders the tweet when it's live)
    (dict(body_text="suspended account", selectors={ARTICLE: FakeEl()}), "Live"),
])
async def test_twitter_detection(kw, expected):
    result = await _scraper()._detect_status(FakeTab(**kw), "")
    if expected is None:
        assert result is None
    else:
        assert result is not None and result[0] == expected
