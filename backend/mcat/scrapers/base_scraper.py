import random
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

from core.driver_manager import WebDriverPool


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
    """Shared scraping harness for pooled, signal-based platform scrapers.

    The per-URL flow lives here once: check out a driver, rate-limit, load the
    page, dismiss the consent modal, poll for a conclusive detection signal,
    screenshot, retry on transient errors, and honor pause/cancel. Subclasses
    supply only the platform-specific pieces:

      - get_platform_name()             (required)
      - _extract_id(url)                short id for logs + screenshot names
      - _dismiss_consent(driver)        click-through fallback for the cookie modal
      - _detect_status(driver, title)   the actual page inspection / triage

    The scraper instance is shared across worker threads, so no per-URL state is
    stored on self; the page title is threaded through as a parameter.
    """

    cancel_event: threading.Event | None = None
    pause_event: threading.Event | None = None

    # Rate limiting bounds in seconds (subclasses override).
    RATE_LIMIT_MIN: float = 1.0
    RATE_LIMIT_MAX: float = 3.0

    # Timeouts / retries (subclasses may override).
    DRIVER_POOL_TIMEOUT: int = 30    # max wait for a pooled driver
    SIGNAL_TIMEOUT: int = 15         # max wait for any detection signal after load
    SIGNAL_POLL_INTERVAL: float = 0.5
    MAX_RETRIES: int = 2
    RETRY_DELAY: float = 2.0

    def __init__(self, driver_pool: WebDriverPool, log_callback: Callable | None = None) -> None:
        self.driver_pool: WebDriverPool = driver_pool
        self._log_callback: Callable | None = log_callback
        self.pause_event: threading.Event | None = None
        self.save_screenshots: bool = False
        self.screenshot_base_path: Path | None = None
        self.min_delay: float = self.RATE_LIMIT_MIN
        self.max_delay: float = self.RATE_LIMIT_MAX
        self.last_request_time: float = 0.0
        self._rate_lock: threading.Lock = threading.Lock()

    # --- platform hooks ---

    @abstractmethod
    def get_platform_name(self) -> str:
        ...

    def _extract_id(self, url: str) -> str:
        """Short id used in log lines and screenshot filenames. Override per platform."""
        return url.rstrip("/").split("/")[-1][:20]

    def _dismiss_consent(self, driver: WebDriver) -> None:
        """Dismiss the platform's cookie-consent modal (fallback). Override per platform."""
        pass

    def _detect_status(self, driver: WebDriver, initial_title: str = "") -> StatusResult | None:
        """Inspect the current page; return (status, info) or None to keep polling."""
        raise NotImplementedError

    # --- cancel / pause / logging ---

    def set_cancel_event(self, cancel_event: threading.Event) -> None:
        self.cancel_event = cancel_event

    def set_pause_event(self, pause_event: threading.Event) -> None:
        self.pause_event = pause_event

    def is_cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()

    def _check_pause(self) -> None:
        if self.pause_event:
            # Block until resumed (cheaper than polling).
            self.pause_event.wait()

    def _log(self, message: str, level: str = "info") -> None:
        if self.is_cancelled():
            return
        if self._log_callback:
            self._log_callback(message, level)
        print(message)

    def _apply_rate_limit(self) -> None:
        """Throttle requests across all worker threads sharing this scraper.

        One instance is shared by every worker, so the lock is held through the
        sleep: the shared timestamp acts as a true global spacer instead of
        letting workers read it together and fire in a burst.
        """
        with self._rate_lock:
            delay = random.uniform(self.min_delay, self.max_delay)
            wait = delay - (time.time() - self.last_request_time)
            if wait > 0:
                time.sleep(wait)
            self.last_request_time = time.time()

    # --- screenshots ---

    def enable_screenshots(self, enabled: bool, base_path: str) -> None:
        self.save_screenshots = enabled
        if enabled:
            self.screenshot_base_path = Path(base_path) / "screenshots"

    def _save_screenshot(self, driver: WebDriver, url: str, status: str) -> str:
        if not self.screenshot_base_path:
            return ""
        try:
            rid = self._extract_id(url)
            screenshot_dir = self.screenshot_base_path / status.lower()
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = screenshot_dir / f"{rid}_{timestamp}.png"
            driver.save_screenshot(str(filepath))
            print(f"Screenshot saved: {filepath.name}")
            return str(filepath)
        except Exception as e:
            print(f"Warning: Screenshot failed for {url}: {e}")
            return ""

    # --- shared harness ---

    def check_url_status(self, url: str) -> ScrapingResult:
        """Check a URL with automatic retries on transient errors."""
        result = ScrapingResult(url=url)
        for attempt in range(self.MAX_RETRIES + 1):
            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            result = self._check_url_once(url)

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
                time.sleep(0.1)
        return result

    def _check_url_once(self, url: str) -> ScrapingResult:
        rid = self._extract_id(url)
        result = ScrapingResult(url=url)

        if self.is_cancelled():
            result.status = "Cancelled"
            result.info = "Processing was cancelled"
            return result

        driver = None
        try:
            driver = self.driver_pool.get_driver(timeout=self.DRIVER_POOL_TIMEOUT)

            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            self._check_pause()
            self._apply_rate_limit()

            # Load page; on timeout keep going and inspect whatever rendered.
            self._log(f"Loading page ({rid})")
            try:
                driver.get(url)
            except TimeoutException:
                self._log(f"Page load timed out, checking partial content ({rid})", "warning")

            # Capture the title before any consent redirect can replace it
            # (YouTube does this); platforms that ignore it just don't read it.
            initial_title = ""
            try:
                initial_title = driver.title or ""
            except Exception:
                pass

            self._dismiss_consent(driver)

            self._log(f"Waiting for signals ({rid})")
            detection = self._poll_for_signals(driver, initial_title)

            if detection is not None:
                result.status, result.info = detection
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            result.status = "Unknown"
            result.info = "N/A"
            self._log(f"No signal after {self.SIGNAL_TIMEOUT}s ({rid})", "warning")
            if self.save_screenshots:
                result.screenshot_path = self._save_screenshot(driver, url, result.status)
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
            if driver:
                if self.is_cancelled():
                    pass  # pool shutdown will clean up
                else:
                    try:
                        driver.current_url  # cheap responsiveness check
                        self.driver_pool.return_driver(driver)
                    except Exception as e:
                        print(f"Warning: Driver unresponsive, discarding: {e}")

    def _poll_for_signals(self, driver: WebDriver, initial_title: str = "") -> StatusResult | None:
        """Poll _detect_status until a conclusive signal appears or timeout."""
        start = time.time()
        while (time.time() - start) < self.SIGNAL_TIMEOUT:
            if self.is_cancelled():
                return ("Cancelled", "Processing was cancelled")
            self._check_pause()
            detection = self._detect_status(driver, initial_title)
            if detection is not None:
                return detection
            time.sleep(self.SIGNAL_POLL_INTERVAL)
        return None

    def cleanup(self) -> None:
        """Per-scraper cleanup; the driver pool cleans itself up."""
        pass
