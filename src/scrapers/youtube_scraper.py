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
from cookies.youtube_cookie_handler import dismiss_youtube_cookies


class YouTubeScraper(BaseScraper):
    """YouTube video status checker with pooled drivers and rate limiting."""

    # Rate limiting configuration
    RATE_LIMIT_MIN = 1.0  # Minimum delay between requests (seconds)
    RATE_LIMIT_MAX = 3.0  # Maximum delay between requests (seconds)

    # Timeout configuration
    DRIVER_POOL_TIMEOUT = 30   # Max wait for available driver (seconds)
    PAGE_LOAD_TIMEOUT = 15     # Max wait for page load (seconds)
    SPA_RENDER_WAIT = 10       # Max wait for SPA to render (seconds)

    # Retry configuration
    MAX_RETRIES = 2            # Number of retry attempts on errors
    RETRY_DELAY = 2.0          # Delay between retries (seconds)

    def __init__(self, driver_pool):
        """Initialize with a WebDriver pool instead of manager."""
        self.driver_pool = driver_pool
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
            print(f"📷 Screenshot saved: {filepath.name}")
            return str(filepath)

        except Exception as e:
            print(f"⚠️ Screenshot failed for {url}: {e}")
            return ""

    def check_url_status(self, url: str) -> ScrapingResult:
        """Check URL status with automatic retries on transient failures."""
        for attempt in range(self.MAX_RETRIES + 1):
            result = self._check_url_once(url)

            # Retry only on errors (network issues, timeouts)
            # Don't retry on valid statuses (Removed, Live, etc.)
            if result.status != "Error":
                return result

            # Last attempt - return error result
            if attempt == self.MAX_RETRIES:
                return result

            # Wait before retry
            print(f"⚠️ Retry {attempt + 1}/{self.MAX_RETRIES} for {url}: {result.error_message}")
            time.sleep(self.RETRY_DELAY)

        return result

    def _check_url_once(self, url: str) -> ScrapingResult:
        """Check the status of a YouTube video using pooled driver."""
        print(f"🔍 Checking YouTube URL: {url}")

        result = ScrapingResult()
        result.url = url
        result.platform = self.get_platform_name()

        driver = None
        try:
            # Get driver from pool first (blocking if pool empty)
            driver = self.driver_pool.get_driver(timeout=self.DRIVER_POOL_TIMEOUT)

            # Check if processing is paused (now that we have driver)
            self._check_pause()

            # Apply rate limiting (only when ready to use driver)
            self._apply_rate_limit()

            # Now make the request
            driver.get(url)

            # Dismiss cookie consent modal if present
            dismiss_youtube_cookies(driver, timeout=3)

            # Wait for YouTube's JavaScript to render dynamic content (SPA)
            try:
                WebDriverWait(driver, self.SPA_RENDER_WAIT).until(
                    lambda d: d.title != "YouTube" and len(d.title) > 0
                )
            except TimeoutException:
                pass  # Continue anyway, might be error page

            # Wait for page to load
            try:
                WebDriverWait(driver, self.PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                result.status = "Error"
                result.error_message = "Page load timeout (15s exceeded)"
                print(f"❌ {url}: {result.status} - {result.error_message}")
                return result

            # Check for various YouTube error/restriction indicators
            page_source = driver.page_source.lower()
            
            # Video removed/unavailable
            if any(phrase in page_source for phrase in [
                'video unavailable', 'this video is not available',
                'removed by the user', 'account has been terminated'
            ]):
                result.status = "Removed"
                result.info = "Video unavailable"
                print(f"✅ {url}: {result.status} - {result.info}")
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Age restricted
            if 'age-restricted' in page_source or 'sign in to confirm your age' in page_source:
                result.status = "Age-restricted"
                result.info = "Age verification required"
                print(f"✅ {url}: {result.status} - {result.info}")
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Geo-blocked
            if 'not available in your country' in page_source:
                result.status = "Geo-blocked"
                result.info = "Not available in your region"
                print(f"✅ {url}: {result.status} - {result.info}")
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Private video
            if 'private video' in page_source:
                result.status = "Private"
                result.info = "Video is private"
                print(f"✅ {url}: {result.status} - {result.info}")
                if self.save_screenshots:
                    result.screenshot_path = self._save_screenshot(driver, url, result.status)
                return result

            # Check for content warning panels
            try:
                warning_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="warning"], [class*="restricted"]')
                if warning_elements:
                    warning_text = warning_elements[0].text
                    result.status = "Restricted"
                    result.info = f"Warning: {warning_text[:100]}"
                    print(f"✅ {url}: {result.status} - {result.info}")
                    if self.save_screenshots:
                        result.screenshot_path = self._save_screenshot(driver, url, result.status)
                    return result
            except Exception:
                pass  # Ignore failures in warning element detection

            # If no restrictions found, assume live
            result.status = "Live"
            result.info = "Video available"
            print(f"✅ {url}: {result.status} - {result.info}")
            if self.save_screenshots:
                result.screenshot_path = self._save_screenshot(driver, url, result.status)
            return result

        except Exception as e:
            result.status = "Error"
            result.error_message = str(e)
            print(f"❌ {url}: {result.status} - {result.error_message}")
            return result
        finally:
            # Return driver to pool instead of quitting
            if driver:
                # Validate driver is still responsive before returning to pool
                try:
                    driver.current_url  # Quick check that driver isn't crashed
                    self.driver_pool.return_driver(driver)
                except Exception as e:
                    # Driver is broken, don't return to pool
                    print(f"⚠️ Driver unresponsive, discarding: {e}")
                    # Pool will create new driver when needed
    
    def cleanup(self):
        """Clean up scraper resources."""
        # Pool cleanup is handled by the pool itself
        pass