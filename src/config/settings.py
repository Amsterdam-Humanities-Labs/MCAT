from typing import Dict


class AppConfig:
    """Simple configuration for MCAT application."""
    
    def __init__(self):
        self.scraper_settings = self.load_scraper_settings()
    
    def load_scraper_settings(self) -> Dict:
        """Load scraper settings with defaults."""
        return {
            'timeout': 30,
            'max_workers': 3,
            'headless': True
        }


# Global config instance
config = AppConfig()