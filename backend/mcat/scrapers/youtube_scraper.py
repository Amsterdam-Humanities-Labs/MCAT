from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

from scrapers.base_scraper import BaseScraper, ScrapingResult
from cookies.youtube_cookie_handler import dismiss_youtube_cookies


class YouTubeScraper(BaseScraper):
    """YouTube video status checker with pooled drivers and rate limiting."""

    # Rate limiting configuration
    RATE_LIMIT_MIN = 1.0  # Minimum delay between requests (seconds)
    RATE_LIMIT_MAX = 3.0  # Maximum delay between requests (seconds)

    # Timeout configuration
    DRIVER_POOL_TIMEOUT = 30   # Max wait for available driver (seconds)
    SIGNAL_TIMEOUT = 15        # Max wait for any detection signal after page load (seconds)
    SIGNAL_POLL_INTERVAL = 0.5 # How often to check for signals (seconds)

    # Retry configuration
    MAX_RETRIES = 2            # Number of retry attempts on errors
    RETRY_DELAY = 2.0          # Delay between retries (seconds)

    def __init__(self, driver_pool, log_callback=None):
        """Initialize with a WebDriver pool instead of manager."""
        self.driver_pool = driver_pool
        self._log_callback = log_callback
        # Rate limiting: 1-3 second delay between requests
        self.min_delay = self.RATE_LIMIT_MIN
        self.max_delay = self.RATE_LIMIT_MAX
        self.last_request_time = 0

        # Pause control - event-based instead of polling
        self.pause_event = None

        # Screenshot configuration
        self.save_screenshots: bool = False
        self.screenshot_base_path: Optional[Path] = None

    def get_platform_name(self) -> str:
        """Return the platform name for this scraper."""
        return "youtube"

    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        # Random delay between min_delay and max_delay
        delay = random.uniform(self.min_delay, self.max_delay)

        if time_since_last < delay:
            sleep_time = delay - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _check_pause(self):
        """Check if processing is paused and wait efficiently."""
        if self.pause_event:
            # Block until pause event is cleared (much more efficient than polling)
            self.pause_event.wait()

    def set_pause_event(self, pause_event):
        """Set threading event for pause control."""
        self.pause_event = pause_event

    def _log(self, message: str, level: str = "info"):
        """Log message via callback (to UI) and stdout."""
        if self.is_cancelled():
            return
        if self._log_callback:
            self._log_callback(message, level)
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
            # Extract video ID from URL
            video_id = url.split('v=')[-1].split('&')[0][:20]  # Truncate for safety

            # Create status-specific folder
            screenshot_dir = self.screenshot_base_path / status.lower()
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            # Filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{video_id}_{timestamp}.png"
            filepath = screenshot_dir / filename

            # Save screenshot
            driver.save_screenshot(str(filepath))
            print(f"Screenshot saved: {filepath.name}")
            return str(filepath)

        except Exception as e:
            print(f"Warning: Screenshot failed for {url}: {e}")
            return ""

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
            # Don't retry on valid statuses (Removed, Live, etc.)
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

    @staticmethod
    def _video_id(url: str) -> str:
        return url.split('v=')[-1].split('&')[0]

    def _check_url_once(self, url: str) -> ScrapingResult:
        """Check the status of a YouTube video using pooled driver."""
        vid = self._video_id(url)
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

            # Check if processing is paused (now that we have driver)
            self._check_pause()

            # Apply rate limiting (only when ready to use driver)
            self._apply_rate_limit()

            # Load page — if it times out, continue anyway and poll
            # for whatever content did load (YouTube SPA may partially render)
            self._log(f"Loading page ({vid})")
            try:
                driver.get(url)
            except TimeoutException:
                self._log(f"Page load timed out, checking partial content ({vid})", "warning")

            # Dismiss cookie consent modal if present
            dismiss_youtube_cookies(driver, timeout=3)

            # Poll for detection signals instead of fixed sleeps.
            # Returns as soon as any conclusive signal is found.
            self._log(f"Waiting for signals ({vid})")
            detection = self._poll_for_signals(driver)

            if detection is not None:
                result.status, result.info = detection
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # No signal after full timeout
            result.status = "Unknown"
            result.info = ""
            self._log(f"No signal after {self.SIGNAL_TIMEOUT}s ({vid})", "warning")
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
                self._log(f"Error: {result.error_message} ({vid})", "error")
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

    REMOVAL_PHRASES = (
        'video unavailable', 'this video is not available',
        "this video isn't available", "video isn't available anymore",
        'removed by the user', 'account has been terminated',
    )

    def _detect_status(self, driver):
        """
        Check all detection signals on the current page state.

        Returns (status, info) if a conclusive signal is found, or None
        if no signal is present yet (keep polling).

        Triage order matters: negative signals (removal/restriction) are
        checked before positive signals (Live) so we never conclude Live
        before a removal notice has had a chance to appear.
        """
        # Get visible text (not raw HTML which contains JS template strings)
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        except Exception:
            return None  # Page not ready yet

        # --- Negative signals (positive evidence of removal/restriction) ---

        if any(phrase in page_text for phrase in self.REMOVAL_PHRASES):
            return ("Removed", "Video unavailable")

        if 'age-restricted' in page_text or 'sign in to confirm your age' in page_text:
            return ("Age-restricted", "Age verification required")

        if 'not available in your country' in page_text:
            return ("Geo-blocked", "Not available in your region")

        if 'private video' in page_text:
            return ("Private", "Video is private")

        # Warning/restricted elements
        try:
            warning_elements = driver.find_elements(
                By.CSS_SELECTOR, '[class*="warning"], [class*="restricted"]'
            )
            for el in warning_elements:
                text = el.text.strip()
                if text:
                    return ("Restricted", f"Warning: {text[:100]}")
        except Exception:
            pass

        # --- Positive signals (evidence the video is live) ---

        # Primary: h1 title element rendered by SPA
        try:
            title_el = driver.find_element(
                By.CSS_SELECTOR, 'h1.ytd-watch-metadata, h1.title'
            )
            if title_el.text.strip():
                return ("Live", "Video available")
        except Exception:
            pass

        # Fallback: page title set to "<Video Title> - YouTube"
        # This updates from server-rendered HTML before SPA components mount,
        # so it works even when the h1 element never renders (slow connections).
        # Removed videos keep the bare title "YouTube".
        try:
            title = driver.title
            if title and title != "YouTube" and " - YouTube" in title:
                return ("Live", "Video available")
        except Exception:
            pass

        return None

    def _poll_for_signals(self, driver):
        """
        Poll _detect_status until a conclusive signal is found or timeout.

        Returns (status, info) or None if timeout expired with no signal.
        """
        start = time.time()
        while (time.time() - start) < self.SIGNAL_TIMEOUT:
            if self.is_cancelled():
                return ("Cancelled", "Processing was cancelled")

            detection = self._detect_status(driver)
            if detection is not None:
                return detection

            time.sleep(self.SIGNAL_POLL_INTERVAL)

        return None

    def cleanup(self):
        """Clean up scraper resources."""
        # Pool cleanup is handled by the pool itself
        pass
