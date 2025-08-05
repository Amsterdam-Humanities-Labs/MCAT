from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


class ScrapingResult:
    """Standardized result format for all scrapers."""
    
    def __init__(self):
        self.url: str = ""
        self.status: str = ""  # "Live", "Removed", "Restricted", "Error"
        self.info: str = ""    # Additional details
        self.timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.error_message: str = ""
        self.platform: str = ""
    
    def to_dict(self) -> dict:
        """Convert result to dictionary for CSV export."""
        return {
            'url': self.url,
            'status': self.status,
            'info': self.info,
            'timestamp': self.timestamp,
            'error_message': self.error_message,
            'platform': self.platform
        }


class BaseScraper(ABC):
    """Abstract base class for all platform scrapers."""
    
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
    
    @abstractmethod
    def check_url_status(self, url: str) -> ScrapingResult:
        """Check the status of a single URL."""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name for this scraper."""
        pass
    
    def batch_check(self, urls: List[str]) -> List[ScrapingResult]:
        """Check multiple URLs in batch."""
        results = []
        for url in urls:
            result = self.check_url_status(url)
            results.append(result)
        return results
    
    def cleanup(self):
        """Clean up any resources used by the scraper."""
        pass