from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import BaseScraper, ScrapingResult


class YouTubeScraper(BaseScraper):
    """YouTube video status checker."""
    
    def get_platform_name(self) -> str:
        """Return the platform name for this scraper."""
        return "youtube"
    
    def check_url_status(self, url: str) -> ScrapingResult:
        """Check the status of a YouTube video."""
        result = ScrapingResult()
        result.url = url
        result.platform = self.get_platform_name()
        
        driver = None
        try:
            driver = self.driver_manager.create_driver()
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
            if driver:
                driver.quit()
        
        return result