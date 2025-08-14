from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseScraper, ScrapingResult


class YouTubeScraper(BaseScraper):
    """YouTube video status checker with pooled drivers and rate limiting."""
    
    def __init__(self, driver_pool):
        """Initialize with a WebDriver pool instead of manager."""
        self.driver_pool = driver_pool
        # Rate limiting: 1-3 second delay between requests
        self.min_delay = 1.0
        self.max_delay = 3.0
        self.last_request_time = 0
        
        # Pause control - event-based instead of polling
        self.pause_event = None
    
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
    
    def check_url_status(self, url: str) -> ScrapingResult:
        """Check the status of a YouTube video using pooled driver."""
        result = ScrapingResult()
        result.url = url
        result.platform = self.get_platform_name()
        
        # Check if processing is paused
        self._check_pause()
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        driver = None
        try:
            # Get driver from pool
            driver = self.driver_pool.get_driver(timeout=30)
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for various YouTube error/restriction indicators
            page_source = driver.page_source.lower()
            
            # Video removed/unavailable
            if any(phrase in page_source for phrase in [
                'video unavailable', 'this video is not available', 
                'removed by the user', 'account has been terminated'
            ]):
                result.status = "Removed"
                result.info = "Video unavailable"
                return result
            
            # Age restricted
            if 'age-restricted' in page_source or 'sign in to confirm your age' in page_source:
                result.status = "Age-restricted"
                result.info = "Age verification required"
                return result
            
            # Geo-blocked
            if 'not available in your country' in page_source:
                result.status = "Geo-blocked"
                result.info = "Not available in your region"
                return result
            
            # Private video
            if 'private video' in page_source:
                result.status = "Private"
                result.info = "Video is private"
                return result
            
            # Check for content warning panels
            try:
                warning_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="warning"], [class*="restricted"]')
                if warning_elements:
                    warning_text = warning_elements[0].text
                    result.status = "Restricted"
                    result.info = f"Warning: {warning_text[:100]}"
                    return result
            except:
                pass
            
            # If no restrictions found, assume live
            result.status = "Live"
            result.info = "Video available"
            return result
            
        except Exception as e:
            result.status = "Error"
            result.error_message = str(e)
            return result
        finally:
            # Return driver to pool instead of quitting
            if driver:
                self.driver_pool.return_driver(driver)
        
        return result
    
    def cleanup(self):
        """Clean up scraper resources."""
        # Pool cleanup is handled by the pool itself
        pass