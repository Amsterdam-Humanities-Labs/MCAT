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


class InstagramScraper(BaseScraper):
    """Instagram post status checker with pooled drivers and rate limiting."""

    # Rate limiting configuration
    RATE_LIMIT_MIN = 1.5  # Minimum delay between requests (seconds)
    RATE_LIMIT_MAX = 3.5  # Maximum delay between requests (seconds)

    # Timeout configuration
    DRIVER_POOL_TIMEOUT = 30   # Max wait for available driver (seconds)
    PAGE_LOAD_TIMEOUT = 15     # Max wait for page load (seconds)
    SPA_RENDER_WAIT = 3        # Wait for Instagram SPA to render (seconds)

    # Retry configuration
    MAX_RETRIES = 2            # Number of retry attempts on errors
    RETRY_DELAY = 2.0          # Delay between retries (seconds)

    # Known error patterns for detection
    ERROR_KEYWORDS = [
        "isn't available",
        "not available",
        "broken",
        "removed",
        "sorry",
        "page not found",
        "content not found"
    ]

    def __init__(self, driver_pool):
        """Initialize with a WebDriver pool."""
        self.driver_pool = driver_pool
        self.min_delay = self.RATE_LIMIT_MIN
        self.max_delay = self.RATE_LIMIT_MAX
        self.last_request_time = 0

        # Pause control - event-based
        self.pause_event = None

        # Screenshot configuration
        self.save_screenshots: bool = False
        self.screenshot_base_path: Optional[Path] = None

    def get_platform_name(self) -> str:
        """Return the platform name for this scraper."""
        return "instagram"

    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        delay = random.uniform(self.min_delay, self.max_delay)

        if time_since_last < delay:
            sleep_time = delay - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _check_pause(self):
        """Check if processing is paused and wait efficiently."""
        if self.pause_event:
            self.pause_event.wait()

    def set_pause_event(self, pause_event):
        """Set threading event for pause control."""
        self.pause_event = pause_event

    def _log(self, message: str):
        """Print message only if not cancelled."""
        if not self.is_cancelled():
            print(message)

    def enable_screenshots(self, enabled: bool, base_path: str) -> None:
        """
        Enable screenshot saving with base path.

        Args:
            enabled: Whether to save screenshots
            base_path: Base directory path for screenshot storage
        """
        self.save_screenshots = enabled
        if enabled:
            self.screenshot_base_path = Path(base_path) / "screenshots"

    def _save_screenshot(self, driver, url: str, status: str) -> str:
        """
        Save screenshot for evidence.

        Args:
            driver: WebDriver instance
            url: URL being checked
            status: Status result (Live, Removed, etc.)

        Returns:
            Path to saved screenshot file, or empty string if failed
        """
        if not self.screenshot_base_path:
            return ""

        try:
            # Extract post ID from URL (handle /p/, /reel/, /tv/ formats)
            post_id = self._extract_post_id(url)

            # Create status-specific folder
            screenshot_dir = self.screenshot_base_path / status.lower()
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            # Filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{post_id}_{timestamp}.png"
            filepath = screenshot_dir / filename

            # Save screenshot
            driver.save_screenshot(str(filepath))
            print(f"Screenshot saved: {filepath.name}")
            return str(filepath)

        except Exception as e:
            print(f"Warning: Screenshot failed for {url}: {e}")
            return ""

    def _extract_post_id(self, url: str) -> str:
        """Extract post ID from Instagram URL."""
        try:
            # Handle various Instagram URL formats:
            # https://www.instagram.com/p/ABC123/
            # https://www.instagram.com/reel/ABC123/
            # https://www.instagram.com/tv/ABC123/
            parts = url.rstrip('/').split('/')
            for i, part in enumerate(parts):
                if part in ('p', 'reel', 'tv') and i + 1 < len(parts):
                    return parts[i + 1][:20]  # Truncate for safety
            return url.split('/')[-1][:20]
        except Exception:
            return "unknown"

    def check_url_status(self, url: str) -> ScrapingResult:
        """Check URL status with automatic retries on transient failures."""
        for attempt in range(self.MAX_RETRIES + 1):
            # Check for cancellation before each attempt
            if self.is_cancelled():
                result = ScrapingResult()
                result.url = url
        
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            result = self._check_url_once(url)

            # Retry only on errors (network issues, timeouts)
            if result.status != "Error":
                return result

            # Last attempt - return error result
            if attempt == self.MAX_RETRIES:
                return result

            # Wait before retry (check for cancellation during wait)
            print(f"Warning: Retry {attempt + 1}/{self.MAX_RETRIES} for {url}: {result.error_message}")
            for _ in range(int(self.RETRY_DELAY * 10)):  # Check every 0.1s
                if self.is_cancelled():
                    result.status = "Cancelled"
                    result.info = "Processing was cancelled"
                    return result
                time.sleep(0.1)

        return result

    def _check_url_once(self, url: str) -> ScrapingResult:
        """Check the status of an Instagram post using pooled driver."""
        self._log(f"Checking Instagram URL: {url}")

        result = ScrapingResult()
        result.url = url


        # Early cancellation check
        if self.is_cancelled():
            result.status = "Cancelled"
            result.info = "Processing was cancelled"
            return result

        driver = None
        try:
            # Get driver from pool first (blocking if pool empty)
            driver = self.driver_pool.get_driver(timeout=self.DRIVER_POOL_TIMEOUT)

            # Check for cancellation after getting driver
            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            # Check if processing is paused
            self._check_pause()

            # Apply rate limiting
            self._apply_rate_limit()

            # Navigate to URL
            driver.get(url)

            # Wait for Instagram SPA to render
            time.sleep(self.SPA_RENDER_WAIT)

            # Check for cancellation after page load (before detection)
            if self.is_cancelled():
                result.status = "Cancelled"
                result.info = "Processing was cancelled"
                return result

            # Strategy 1: Look for error SVG icon
            if self._check_error_svg(driver, result):
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Strategy 2: Look for specific text content in page
            if self._check_error_text(driver, result):
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Strategy 3: Look for error container divs
            if self._check_error_containers(driver, result):
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Strategy 4: Check for main article element (indicates normal post)
            if self._check_article_exists(driver):
                result.status = "Live"
                result.info = "Post available"
                self._log(f"OK: {url}: {result.status} - {result.info}")
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

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
                    pass  # Driver will be cleaned up by pool shutdown
                else:
                    try:
                        driver.current_url
                        self.driver_pool.return_driver(driver)
                    except Exception as e:
                        print(f"Warning: Driver unresponsive, discarding: {e}")

    def _check_error_svg(self, driver, result: ScrapingResult) -> bool:
        """Check for Instagram error SVG icon."""
        try:
            driver.find_element(By.CSS_SELECTOR, 'svg[aria-label="error"]')
            # Error icon found - extract message
            error_messages = self._extract_error_messages(driver)
            if error_messages:
                result.status = "Removed"
                result.info = " | ".join(error_messages[:2])
            else:
                result.status = "Removed"
                result.info = "Post unavailable"
            self._log(f"OK: {result.url}: {result.status} - {result.info}")
            return True
        except Exception:
            return False

    def _check_error_text(self, driver, result: ScrapingResult) -> bool:
        """Check for specific error text patterns in visible page text."""
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()

            # Check for post unavailable messages
            if "post isn't available" in page_text or "post isn't available" in page_text:
                messages = self._extract_error_messages(driver)
                result.status = "Removed"
                result.info = " | ".join(messages) if messages else "Post isn't available"
                self._log(f"OK: {result.url}: {result.status} - {result.info}")
                return True

            # Check for page unavailable
            if "sorry, this page isn't available" in page_text:
                result.status = "Removed"
                result.info = "Page isn't available"
                self._log(f"OK: {result.url}: {result.status} - {result.info}")
                return True

            # Check for page not found
            if "page not found" in page_text:
                result.status = "Removed"
                result.info = "Page not found"
                self._log(f"OK: {result.url}: {result.status} - {result.info}")
                return True

            return False
        except Exception:
            return False

    def _check_error_containers(self, driver, result: ScrapingResult) -> bool:
        """Check for error container divs with specific class patterns."""
        try:
            error_containers = driver.find_elements(
                By.CSS_SELECTOR,
                'div.x9f619.xjbqb8w.x78zum5'
            )

            for container in error_containers:
                text = container.text.strip()
                if text and any(keyword in text.lower() for keyword in self.ERROR_KEYWORDS):
                    result.status = "Removed"
                    result.info = text[:100]  # Truncate long messages
                    self._log(f"OK: {result.url}: {result.status} - {result.info}")
                    return True

            return False
        except Exception:
            return False

    def _check_article_exists(self, driver) -> bool:
        """Check if main article element exists (indicates normal post)."""
        try:
            driver.find_element(By.CSS_SELECTOR, 'article[role="presentation"]')
            return True
        except Exception:
            return False

    def _extract_error_messages(self, driver) -> list:
        """Extract error messages from page using Selenium."""
        try:
            error_messages = []
            spans = driver.find_elements(By.CSS_SELECTOR, 'span[dir="auto"]')

            for span in spans:
                text = span.text.strip()
                if text and len(text) > 5:
                    if any(keyword in text.lower() for keyword in self.ERROR_KEYWORDS):
                        error_messages.append(text)

            return error_messages
        except Exception:
            return []

    def cleanup(self):
        """Clean up scraper resources."""
        pass
