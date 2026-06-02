from collections.abc import Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
import threading
import time
from pathlib import Path
from datetime import datetime

from scrapers.base_scraper import BaseScraper, ScrapingResult
from core.driver_manager import WebDriverPool
from cookies.instagram_cookie_handler import dismiss_instagram_cookies


class InstagramScraper(BaseScraper):
    """Instagram post status checker with pooled drivers and rate limiting."""

    # Rate limiting configuration
    RATE_LIMIT_MIN = 1.5  # Minimum delay between requests (seconds)
    RATE_LIMIT_MAX = 3.5  # Maximum delay between requests (seconds)

    # Timeout configuration
    DRIVER_POOL_TIMEOUT = 30   # Max wait for available driver (seconds)
    SIGNAL_TIMEOUT = 15        # Max wait for any detection signal after page load (seconds)
    SIGNAL_POLL_INTERVAL = 0.5 # How often to check for signals (seconds)

    # Retry configuration
    MAX_RETRIES = 2            # Number of retry attempts on errors
    RETRY_DELAY = 2.0          # Delay between retries (seconds)

    REMOVAL_PHRASES = (
        "post isn't available",
        "sorry, this page isn't available",
        "this page isn't available",
        "page not found",
        "content isn't available",
    )

    def __init__(self, driver_pool: WebDriverPool, log_callback: Callable | None = None):
        super().__init__()
        self.driver_pool: WebDriverPool = driver_pool
        self._log_callback: Callable | None = log_callback
        self.pause_event: threading.Event | None = None
        self.save_screenshots: bool = False
        self.screenshot_base_path: Path | None = None

    def get_platform_name(self) -> str:
        return "instagram"

    def _check_pause(self) -> None:
        if self.pause_event:
            self.pause_event.wait()

    def set_pause_event(self, pause_event: threading.Event) -> None:
        self.pause_event = pause_event

    def _log(self, message: str, level: str = "info") -> None:
        if self.is_cancelled():
            return
        if self._log_callback:
            self._log_callback(message, level)
        print(message)

    def enable_screenshots(self, enabled: bool, base_path: str) -> None:
        self.save_screenshots = enabled
        if enabled:
            self.screenshot_base_path = Path(base_path) / "screenshots"

    def _save_screenshot(self, driver: WebDriver, url: str, status: str) -> str:
        if not self.screenshot_base_path:
            return ""
        try:
            post_id = self._post_id(url)
            screenshot_dir = self.screenshot_base_path / status.lower()
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = screenshot_dir / f"{post_id}_{timestamp}.png"
            driver.save_screenshot(str(filepath))
            print(f"Screenshot saved: {filepath.name}")
            return str(filepath)
        except Exception as e:
            print(f"Warning: Screenshot failed for {url}: {e}")
            return ""

    @staticmethod
    def _post_id(url: str) -> str:
        try:
            parts = url.rstrip('/').split('/')
            for i, part in enumerate(parts):
                if part in ('p', 'reel', 'tv') and i + 1 < len(parts):
                    return parts[i + 1][:20]
            return url.split('/')[-1][:20]
        except Exception:
            return "unknown"

    def check_url_status(self, url: str) -> ScrapingResult:
        result = ScrapingResult(url=url)
        for attempt in range(self.MAX_RETRIES + 1):
            if self.is_cancelled():
                result = ScrapingResult()
                result.url = url
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            result = self._check_url_once(url)

            if result.status != "Error":
                return result

            if attempt == self.MAX_RETRIES:
                return result

            print(f"Warning: Retry {attempt + 1}/{self.MAX_RETRIES} for {url}: {result.error_message}")
            for _ in range(int(self.RETRY_DELAY * 10)):
                if self.is_cancelled():
                    result.status = "Cancelled"
                    result.info = "Processing was cancelled"
                    return result
                time.sleep(0.1)

        return result

    def _check_url_once(self, url: str) -> ScrapingResult:
        pid = self._post_id(url)
        result = ScrapingResult()
        result.url = url

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

            self._log(f"Loading page ({pid})")
            try:
                driver.get(url)
            except TimeoutException:
                self._log(f"Page load timed out, checking partial content ({pid})", "warning")

            dismiss_instagram_cookies(driver, timeout=3)

            self._log(f"Waiting for signals ({pid})")
            detection = self._poll_for_signals(driver)

            if detection is not None:
                result.status, result.info = detection
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            result.status = "Unknown"
            result.info = "N/A"
            self._log(f"No signal after {self.SIGNAL_TIMEOUT}s ({pid})", "warning")
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
                self._log(f"Error: {result.error_message} ({pid})", "error")
            return result
        finally:
            if driver:
                if self.is_cancelled():
                    pass
                else:
                    try:
                        driver.current_url
                        self.driver_pool.return_driver(driver)
                    except Exception as e:
                        print(f"Warning: Driver unresponsive, discarding: {e}")

    def _detect_status(self, driver: WebDriver) -> tuple[str, str] | None:
        """
        Check all detection signals on current page state.
        Returns (status, info) or None if no signal yet.

        Triage: negative signals first, then positive, then login detection.
        """
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        except Exception:
            return None

        # --- Negative signals ---

        # Page title check
        try:
            title = driver.title
            if title and "isn't available" in title.lower():
                return ("Removed", title)
        except Exception:
            pass

        # Error SVG icon
        try:
            driver.find_element(By.CSS_SELECTOR, 'svg[aria-label="error"]')
            return ("Removed", "error icon displayed")
        except Exception:
            pass

        # Error text in body
        for phrase in self.REMOVAL_PHRASES:
            if phrase in page_text:
                return ("Removed", phrase)

        # --- Positive signals ---

        # og:title meta tag — reliable even in logged-out view
        try:
            meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
            content = meta.get_attribute("content")
            if content and " on Instagram:" in content:
                return ("Live", "N/A")
        except Exception:
            pass

        # article element — works when logged in
        try:
            driver.find_element(By.CSS_SELECTOR, 'article[role="presentation"]')
            return ("Live", "N/A")
        except Exception:
            pass

        # --- Login detection ---

        if "log in" in page_text and "sign up" in page_text:
            return ("Login Required", "N/A")

        return None

    def _poll_for_signals(self, driver: WebDriver) -> tuple[str, str] | None:
        start = time.time()
        while (time.time() - start) < self.SIGNAL_TIMEOUT:
            if self.is_cancelled():
                return ("Cancelled", "Processing was cancelled")
            self._check_pause()

            detection = self._detect_status(driver)
            if detection is not None:
                return detection

            time.sleep(self.SIGNAL_POLL_INTERVAL)

        return None

    def cleanup(self) -> None:
        pass
