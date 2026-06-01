from collections.abc import Callable
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import TimeoutException
import time
import random
from pathlib import Path
from datetime import datetime

from scrapers.base_scraper import BaseScraper, ScrapingResult
from core.driver_manager import WebDriverPool
from cookies.facebook_cookie_handler import dismiss_facebook_cookies


class FacebookScraper(BaseScraper):
    """Facebook post status checker with pooled drivers and rate limiting."""

    RATE_LIMIT_MIN = 1.5
    RATE_LIMIT_MAX = 3.5

    DRIVER_POOL_TIMEOUT = 30
    SIGNAL_TIMEOUT = 15
    SIGNAL_POLL_INTERVAL = 0.5

    MAX_RETRIES = 2
    RETRY_DELAY = 2.0

    REMOVAL_PHRASES = (
        "this content isn't available",
        "this page isn't available",
        "content isn't available right now",
        "sorry, this content isn't available",
        "the link you followed may be broken",
        "page not found",
        "this content has been removed",
    )

    def __init__(self, driver_pool: WebDriverPool, log_callback: Callable | None = None):
        self.driver_pool = driver_pool
        self._log_callback: Callable | None = log_callback
        self.min_delay: float = self.RATE_LIMIT_MIN
        self.max_delay: float = self.RATE_LIMIT_MAX
        self.last_request_time: float = 0
        self.save_screenshots: bool = False
        self.screenshot_base_path: Path | None = None

    def get_platform_name(self) -> str:
        return "facebook"

    def _apply_rate_limit(self) -> None:
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
        self.last_request_time = time.time()

    def _check_pause(self) -> None:
        if self.pause_event:
            self.pause_event.wait()

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
            if "fbid=" in url:
                return url.split("fbid=")[1].split("&")[0][:20]
            if "story_fbid=" in url:
                return url.split("story_fbid=")[1].split("&")[0][:20]
            if "?v=" in url:
                return url.split("?v=")[1].split("&")[0][:20]
            parts = url.rstrip("/").split("/")
            for i, part in enumerate(parts):
                if part in ("posts", "videos", "reel", "permalink") and i + 1 < len(parts):
                    return parts[i + 1].split("?")[0][:20]
            return parts[-1].split("?")[0][:20]
        except Exception:
            return "unknown"

    def check_url_status(self, url: str) -> ScrapingResult:
        result = ScrapingResult(url=url)
        for attempt in range(self.MAX_RETRIES + 1):
            if self.is_cancelled():
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

            dismiss_facebook_cookies(driver, timeout=3)

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

        Triage: negative signals first, then positive.
        """
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        except Exception:
            return None

        # --- Negative signals ---

        for phrase in self.REMOVAL_PHRASES:
            if phrase in page_text:
                return ("Removed", phrase)

        # --- Positive signals ---

        # Article element
        try:
            driver.find_element(By.CSS_SELECTOR, 'div[role="article"]')
            return ("Live", "N/A")
        except Exception:
            pass

        # og:title meta tag
        try:
            meta = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:title"]')
            content = meta.get_attribute("content")
            if content:
                return ("Live", "N/A")
        except Exception:
            pass

        # Page title pattern: "Post text - Page Name | Facebook"
        try:
            title = driver.title
            if title and title != "Facebook" and " | Facebook" in title:
                return ("Live", "N/A")
        except Exception:
            pass

        # --- Login detection ---

        if "log in" in page_text and "create new account" in page_text:
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
