import asyncio
import random
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from zendriver.core.tab import Tab

from core.browser_manager import BrowserSession


# A conclusive detection outcome: (status, info). Aliased rather than made a
# NamedTuple because it is always immediately unpacked into ScrapingResult
# (`result.status, result.info = detection`) and never field-accessed, so the
# alias documents the 5 detection signatures without churning every return site.
StatusResult = tuple[str, str]


@dataclass
class ScrapingResult:
    """Standardized result format for all scrapers."""

    url: str = ""
    status: str = ""
    info: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    error_message: str = ""
    screenshot_path: str = ""


class BaseScraper(ABC):
    """Shared async scraping harness for tab-pooled, signal-based scrapers.

    The per-URL flow lives here once: check out a tab, rate-limit, load the page,
    poll for a conclusive detection signal, screenshot, retry on transient errors,
    and honor pause/cancel. Subclasses supply only the platform-specific pieces:

      - get_platform_name()           (required)
      - _extract_id(url)              short id for logs + screenshot names (sync)
      - _detect_status(tab, title)    the actual page inspection / triage

    Consent modals are never dismissed in-scraper: the per-project cookie jar,
    captured during Set up browser, is injected and suppresses them.

    One instance is shared across the concurrent tab coroutines, so no per-URL
    state is stored on self; the page title is threaded through as a parameter.
    Pause/cancel use threading.Events (set from the worker/HTTP thread) and are
    polled between awaits.
    """

    cancel_event: threading.Event | None = None
    pause_event: threading.Event | None = None

    # Rate limiting bounds in seconds (same for every platform).
    RATE_LIMIT_MIN: float = 1.5
    RATE_LIMIT_MAX: float = 3.5

    # Max length of the short id used in log lines and screenshot filenames.
    ID_MAX_LEN: int = 20

    # Timeouts / retries (subclasses may override).
    SIGNAL_TIMEOUT: int = 15         # max wait for any detection signal after load
    SIGNAL_POLL_INTERVAL: float = 0.5
    MAX_RETRIES: int = 2
    RETRY_DELAY: float = 2.0

    # Per-operation timeouts (seconds): bound every zendriver tab/CDP call so a
    # wedged page or connection can't hang the whole batch (a single un-timed
    # await would block asyncio.gather forever, leaving the run stuck and the
    # processing state unable to return to idle — i.e. no further runs).
    PAGE_LOAD_TIMEOUT: float = 30.0
    DETECT_TIMEOUT: float = 8.0
    SCREENSHOT_TIMEOUT: float = 15.0
    EVAL_TIMEOUT: float = 5.0
    SCREENSHOT_SETTLE_TIMEOUT: float = 10.0  # max wait for a Live post to paint (only when screenshotting)
    RENDER_MIN_IMAGE_WIDTH: int = 500        # an image this wide = post media painted (vs avatars/icons)

    def __init__(self, session: BrowserSession, log_callback: Callable | None = None) -> None:
        self.session: BrowserSession = session
        self._log_callback: Callable | None = log_callback
        self.pause_event: threading.Event | None = None
        self.save_screenshots: bool = False
        self.screenshot_base_path: Path | None = None
        self.min_delay: float = self.RATE_LIMIT_MIN
        self.max_delay: float = self.RATE_LIMIT_MAX
        self.last_request_time: float = 0.0
        self._rate_lock: asyncio.Lock = asyncio.Lock()

    # --- platform hooks ---

    @abstractmethod
    def get_platform_name(self) -> str:
        ...

    def _extract_id(self, url: str) -> str:
        """Short id used in log lines and screenshot filenames. Override per platform."""
        return url.rstrip("/").split("/")[-1][:self.ID_MAX_LEN]

    async def _detect_status(self, tab: Tab, initial_title: str = "") -> StatusResult | None:
        """Inspect the current page; return (status, info) or None to keep polling."""
        raise NotImplementedError

    # --- cancel / pause / logging ---

    def set_cancel_event(self, cancel_event: threading.Event) -> None:
        self.cancel_event = cancel_event

    def set_pause_event(self, pause_event: threading.Event) -> None:
        self.pause_event = pause_event

    def is_cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()

    async def _check_pause(self) -> None:
        # pause_event is the resume flag: set = run, clear = paused.
        while self.pause_event is not None and not self.pause_event.is_set():
            await asyncio.sleep(0.1)

    def _log(self, message: str, level: str = "info") -> None:
        if self.is_cancelled():
            return
        if self._log_callback:
            self._log_callback(message, level)
        print(message)

    async def _apply_rate_limit(self) -> None:
        """Throttle requests across all concurrent tab coroutines sharing this
        scraper. The lock is held through the sleep so the shared timestamp acts
        as a true global spacer instead of letting coroutines fire in a burst."""
        async with self._rate_lock:
            delay = random.uniform(self.min_delay, self.max_delay)
            wait = delay - (time.time() - self.last_request_time)
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_request_time = time.time()

    # --- screenshots ---

    def enable_screenshots(self, enabled: bool, base_path: str) -> None:
        self.save_screenshots = enabled
        if enabled:
            self.screenshot_base_path = Path(base_path) / "screenshots"

    async def _save_screenshot(self, tab: Tab, url: str, status: str) -> str:
        if not self.screenshot_base_path:
            return ""
        try:
            rid = self._extract_id(url)
            screenshot_dir = self.screenshot_base_path / status.lower()
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = screenshot_dir / f"{rid}_{timestamp}.png"
            await asyncio.wait_for(tab.save_screenshot(str(filepath)), timeout=self.SCREENSHOT_TIMEOUT)
            print(f"Screenshot saved: {filepath.name}")
            return str(filepath)
        except Exception as e:
            print(f"Warning: Screenshot failed for {url}: {e}")
            return ""

    async def _wait_for_render(self, tab: Tab) -> None:
        """Wait until a post-media-sized image has painted, so a Live-post
        screenshot shows the post rather than a loading skeleton. The width
        threshold separates real post media (wide) from page chrome like avatars
        and icons (small). Returns as soon as one loads; capped by
        SCREENSHOT_SETTLE_TIMEOUT so it never stalls the batch."""
        js = f"[...document.querySelectorAll('img')].some(i => i.naturalWidth > {self.RENDER_MIN_IMAGE_WIDTH})"
        start = time.time()
        while (time.time() - start) < self.SCREENSHOT_SETTLE_TIMEOUT:
            try:
                ready = await asyncio.wait_for(tab.evaluate(js), timeout=self.EVAL_TIMEOUT)
            except Exception:
                ready = False
            if ready:
                return
            await asyncio.sleep(0.4)

    # --- shared harness ---

    async def check_url_status(self, url: str) -> ScrapingResult:
        """Check a URL with automatic retries on transient errors."""
        result = ScrapingResult(url=url)
        for attempt in range(self.MAX_RETRIES + 1):
            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            result = await self._check_url_once(url)

            # Retry only on transient Error; any decided status returns at once.
            if result.status != "Error":
                return result
            if attempt == self.MAX_RETRIES:
                return result

            print(f"Warning: Retry {attempt + 1}/{self.MAX_RETRIES} for {url}: {result.error_message}")
            for _ in range(int(self.RETRY_DELAY * 10)):  # check cancellation every 0.1s
                if self.is_cancelled():
                    result.status = "Cancelled"
                    result.info = "Processing was cancelled"
                    return result
                await asyncio.sleep(0.1)
        return result

    async def _check_url_once(self, url: str) -> ScrapingResult:
        rid = self._extract_id(url)
        result = ScrapingResult(url=url)

        if self.is_cancelled():
            result.status = "Cancelled"
            result.info = "Processing was cancelled"
            return result

        tab = None
        try:
            tab = await self.session.acquire_tab()

            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            await self._check_pause()
            await self._apply_rate_limit()

            # Load page; on timeout/error keep going and inspect whatever rendered.
            self._log(f"Loading page ({rid})")
            try:
                await asyncio.wait_for(tab.get(url), timeout=self.PAGE_LOAD_TIMEOUT)
            except Exception:
                self._log(f"Page load issue, checking partial content ({rid})", "warning")

            # Capture the title before any consent redirect can replace it
            # (YouTube does this); platforms that ignore it just don't read it.
            initial_title = ""
            try:
                initial_title = await asyncio.wait_for(tab.evaluate("document.title"), timeout=self.EVAL_TIMEOUT) or ""
            except Exception:
                pass

            self._log(f"Waiting for signals ({rid})")
            detection = await self._poll_for_signals(tab, initial_title)

            if detection is not None:
                result.status, result.info = detection
                if self.save_screenshots:
                    # Detection can finish (e.g. via an og: meta tag) before the
                    # post image paints; let a Live post render so the screenshot
                    # isn't a skeleton. Removed/restricted pages are already at
                    # their terminal state, so shoot immediately.
                    if result.status == "Live":
                        await self._wait_for_render(tab)
                    result.screenshot_path = await self._save_screenshot(tab, url, result.status)
                return result

            result.status = "Unknown"
            result.info = "N/A"
            self._log(f"No signal after {self.SIGNAL_TIMEOUT}s ({rid})", "warning")
            if self.save_screenshots:
                result.screenshot_path = await self._save_screenshot(tab, url, result.status)
            return result

        except Exception as e:
            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
            else:
                result.status = "Error"
                result.error_message = str(e)
                self._log(f"Error: {result.error_message} ({rid})", "error")
            return result
        finally:
            if tab is not None:
                await self.session.release_tab(tab)

    async def _poll_for_signals(self, tab: Tab, initial_title: str = "") -> StatusResult | None:
        """Poll _detect_status until a conclusive signal appears or timeout."""
        start = time.time()
        while (time.time() - start) < self.SIGNAL_TIMEOUT:
            if self.is_cancelled():
                return ("Cancelled", "Processing was cancelled")
            await self._check_pause()
            try:
                detection = await asyncio.wait_for(
                    self._detect_status(tab, initial_title), timeout=self.DETECT_TIMEOUT)
            except asyncio.TimeoutError:
                detection = None  # wedged detect — retry until SIGNAL_TIMEOUT
            if detection is not None:
                return detection
            await asyncio.sleep(self.SIGNAL_POLL_INTERVAL)
        return None

    def cleanup(self) -> None:
        """Per-scraper cleanup; the browser session is stopped by the batch."""
        pass
