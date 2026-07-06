"""Per-URL harness tests for BaseScraper.check_url_status (FakeSession/FakeTab).

Exercises retry, cancel, poll-until-signal, the no-signal fallback, per-op
timeouts, and screenshot gating — with a subclass whose _detect_status is scripted
and timeouts/rate-limit lowered so tests stay fast.
"""
import asyncio
import threading
import pytest

from scrapers.base_scraper import BaseScraper
from _fakes import FakeTab, FakeSession


class _HarnessScraper(BaseScraper):
    def __init__(self, session, detect):
        super().__init__(session)
        self._detect = detect
        self.min_delay = 0.0
        self.max_delay = 0.0
        self.RETRY_DELAY = 0.0
        self.SIGNAL_TIMEOUT = 0.15
        self.SIGNAL_POLL_INTERVAL = 0.01
        self.DETECT_TIMEOUT = 0.05
        self.PAGE_LOAD_TIMEOUT = 0.5

    def get_platform_name(self):
        return "test"

    async def _detect_status(self, tab, initial_title=""):
        return await self._detect(tab, initial_title)


def _scraper(detect, tab=None):
    return _HarnessScraper(FakeSession(tab or FakeTab()), detect)


async def test_live_happy_path():
    async def detect(tab, it): return ("Live", "N/A")
    assert (await _scraper(detect).check_url_status("http://x")).status == "Live"


async def test_retry_then_success():
    calls = {"n": 0}
    async def detect(tab, it):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("transient")
        return ("Live", "N/A")
    result = await _scraper(detect).check_url_status("http://x")
    assert result.status == "Live"
    assert calls["n"] == 3                       # 2 failed attempts + 1 success


async def test_retry_exhaustion_errors():
    async def detect(tab, it): raise ValueError("boom")
    assert (await _scraper(detect).check_url_status("http://x")).status == "Error"


async def test_cancel_short_circuits():
    ev = threading.Event(); ev.set()
    async def detect(tab, it): return ("Live", "N/A")
    s = _scraper(detect); s.set_cancel_event(ev)
    assert (await s.check_url_status("http://x")).status == "Cancelled"


async def test_no_signal_unknown():
    async def detect(tab, it): return None
    assert (await _scraper(detect).check_url_status("http://x")).status == "Unknown"


async def test_load_failure_no_content_errors():
    # Load failed AND nothing rendered -> Error (we couldn't check the URL), not Unknown.
    async def detect(tab, it): return None
    tab = FakeTab(get_error=asyncio.TimeoutError())
    result = await _scraper(detect, tab).check_url_status("http://x")
    assert result.status == "Error"
    assert "timed out" in result.info


async def test_load_failure_with_signal_keeps_status():
    # Load failed but content still rendered -> the real status wins (no over-flagging).
    async def detect(tab, it): return ("Unavailable", "gone")
    tab = FakeTab(get_error=Exception("net::ERR_ABORTED"))
    result = await _scraper(detect, tab).check_url_status("http://x")
    assert result.status == "Unavailable"


async def test_detect_timeout_does_not_hang():
    async def detect(tab, it): await asyncio.sleep(10)
    assert (await _scraper(detect).check_url_status("http://x")).status == "Unknown"


async def test_poll_until_signal():
    calls = {"n": 0}
    async def detect(tab, it):
        calls["n"] += 1
        return ("Live", "N/A") if calls["n"] >= 3 else None
    result = await _scraper(detect).check_url_status("http://x")
    assert result.status == "Live" and calls["n"] >= 3


async def test_screenshot_saved_for_live(tmp_path):
    async def detect(tab, it): return ("Live", "N/A")
    tab = FakeTab(img_ready=True)
    s = _scraper(detect, tab)
    s.enable_screenshots(True, str(tmp_path))
    result = await s.check_url_status("http://x/abc")
    assert result.status == "Live"
    assert result.screenshot_path != "" and tab.screenshots
