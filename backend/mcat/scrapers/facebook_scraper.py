from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

from scrapers.base_scraper import BaseScraper, ScrapingResult


class FacebookScraper(BaseScraper):
    """Facebook post status checker with pooled drivers and rate limiting."""

    # Rate limiting configuration
    RATE_LIMIT_MIN = 1.5
    RATE_LIMIT_MAX = 3.5

    # Timeout configuration
    DRIVER_POOL_TIMEOUT = 30
    PAGE_LOAD_TIMEOUT = 15
    SPA_RENDER_WAIT = 3

    # Retry configuration
    MAX_RETRIES = 2
    RETRY_DELAY = 2.0

    # CSS class used by Facebook for moderation overlay text
    MODERATION_OVERLAY_SELECTOR = ".xzueoph.x1k70j0n"

    # Known error/unavailable patterns
    UNAVAILABLE_KEYWORDS = [
        "this content isn't available",
        "this page isn't available",
        "content isn't available right now",
        "sorry, this content isn't available",
        "the link you followed may be broken",
        "page not found",
        "this content has been removed",
        "removed by",
    ]

    def __init__(self, driver_pool):
        """Initialize with a WebDriver pool."""
        self.driver_pool = driver_pool
        self.min_delay = self.RATE_LIMIT_MIN
        self.max_delay = self.RATE_LIMIT_MAX
        self.last_request_time = 0

        self.pause_event = None

        self.save_screenshots: bool = False
        self.screenshot_base_path: Optional[Path] = None

    def get_platform_name(self) -> str:
        return "facebook"

    def _apply_rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        delay = random.uniform(self.min_delay, self.max_delay)
        if time_since_last < delay:
            time.sleep(delay - time_since_last)
        self.last_request_time = time.time()

    def _check_pause(self):
        if self.pause_event:
            self.pause_event.wait()

    def set_pause_event(self, pause_event):
        self.pause_event = pause_event

    def _log(self, message: str):
        if not self.is_cancelled():
            print(message)

    def enable_screenshots(self, enabled: bool, base_path: str) -> None:
        self.save_screenshots = enabled
        if enabled:
            self.screenshot_base_path = Path(base_path) / "screenshots"

    def _save_screenshot(self, driver, url: str, status: str) -> str:
        if not self.screenshot_base_path:
            return ""
        try:
            post_id = self._extract_post_id(url)
            screenshot_dir = self.screenshot_base_path / status.lower()
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{post_id}_{timestamp}.png"
            filepath = screenshot_dir / filename
            driver.save_screenshot(str(filepath))
            print(f"Screenshot saved: {filepath.name}")
            return str(filepath)
        except Exception as e:
            print(f"Warning: Screenshot failed for {url}: {e}")
            return ""

    def _extract_post_id(self, url: str) -> str:
        """Extract post ID from Facebook URL.

        Handles formats like:
            /posts/123456
            /videos/123456
            /photo/?fbid=123456
            /watch/?v=123456
            /reel/123456
            /permalink/123456
            /story_fbid=123456
        """
        try:
            # Check for query parameter IDs
            if "fbid=" in url:
                return url.split("fbid=")[1].split("&")[0][:20]
            if "story_fbid=" in url:
                return url.split("story_fbid=")[1].split("&")[0][:20]
            if "?v=" in url:
                return url.split("?v=")[1].split("&")[0][:20]

            # Check for path-based IDs
            parts = url.rstrip("/").split("/")
            for i, part in enumerate(parts):
                if part in ("posts", "videos", "reel", "permalink") and i + 1 < len(parts):
                    return parts[i + 1].split("?")[0][:20]

            # Fall back to last path segment
            return parts[-1].split("?")[0][:20]
        except Exception:
            return "unknown"

    def check_url_status(self, url: str) -> ScrapingResult:
        """Check URL status with automatic retries on transient failures."""
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
        """Check the status of a Facebook post using pooled driver."""
        self._log(f"Checking Facebook URL: {url}")

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

            driver.get(url)

            # Wait for page to load
            try:
                WebDriverWait(driver, self.PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                result.status = "Error"
                result.error_message = "Page load timeout"
                self._log(f"Error: {url}: {result.status} - {result.error_message}")
                return result

            # Wait for Facebook SPA to render
            time.sleep(self.SPA_RENDER_WAIT)

            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            # Strategy 1: Check for moderation overlay text
            if self._check_moderation_overlay(driver, result):
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Strategy 2: Check for unavailable/removed page text
            if self._check_unavailable_text(driver, result):
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Positive check: post article present → Live
            try:
                article = driver.find_element(By.CSS_SELECTOR, 'div[role="article"]')
                if article:
                    result.status = "Live"
                    result.info = "Available"
                    self._log(f"OK: {url}: {result.status} - {result.info}")
                    if self.save_screenshots:
                        result.screenshot_path = self._save_screenshot(driver, url, result.status)
                    return result
            except Exception:
                pass

            # No positive Live indicator, no known error pattern → Unknown
            result.status = "Unknown"
            result.info = ""
            self._log(f"OK: {url}: {result.status} - {result.info}")
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
                self._log(f"Error: {url}: {result.status} - {result.error_message}")
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

    def _check_moderation_overlay(self, driver, result: ScrapingResult) -> bool:
        """Check for Facebook's moderation overlay div."""
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, self.MODERATION_OVERLAY_SELECTOR)
            texts = [el.text.strip() for el in elements if el.text.strip()]
            if texts:
                result.status = "Restricted"
                result.info = " | ".join(texts[:2])
                self._log(f"OK: {result.url}: {result.status} - {result.info}")
                return True
            return False
        except Exception:
            return False

    def _check_unavailable_text(self, driver, result: ScrapingResult) -> bool:
        """Check for content unavailable/removed text patterns."""
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            for keyword in self.UNAVAILABLE_KEYWORDS:
                if keyword in page_text:
                    result.status = "Removed"
                    result.info = keyword.capitalize()
                    self._log(f"OK: {result.url}: {result.status} - {result.info}")
                    return True
            return False
        except Exception:
            return False

    def cleanup(self):
        pass
