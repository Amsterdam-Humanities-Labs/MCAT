"""Detection branch coverage for YouTubeScraper._detect_status (offline, FakeTab)."""
import pytest

from scrapers.youtube_scraper import YouTubeScraper
from _fakes import FakeTab


def _scraper():
    return YouTubeScraper(None)  # session unused by _detect_status


@pytest.mark.parametrize("kw, initial, expected", [
    # negative signals
    (dict(body_text="video unavailable"), "", "Removed"),
    (dict(body_text="this video isn't available"), "", "Removed"),
    (dict(body_text="account has been terminated"), "", "Removed"),
    (dict(body_text="age-restricted"), "", "Age-restricted"),
    (dict(body_text="sign in to confirm your age"), "", "Age-restricted"),
    (dict(body_text="not available in your country"), "", "Geo-blocked"),
    (dict(body_text="private video"), "", "Private"),
    (dict(body_text="ok", warn_text="flagged as restricted"), "", "Restricted"),
    # positive signals
    (dict(body_text="ok", h1_text="Some Video Title"), "", "Live"),
    (dict(body_text="ok", title="My Vid - YouTube"), "", "Live"),
    (dict(body_text="ok", title="YouTube"), "My Vid - YouTube", "Live"),  # initial_title fallback
    # no signal
    (dict(body_text="just a normal page", title="random"), "", None),
    # precedence: removal beats a live-looking h1
    (dict(body_text="video unavailable", h1_text="Some Video Title"), "", "Removed"),
])
async def test_youtube_detection(kw, initial, expected):
    result = await _scraper()._detect_status(FakeTab(**kw), initial)
    if expected is None:
        assert result is None
    else:
        assert result is not None and result[0] == expected
