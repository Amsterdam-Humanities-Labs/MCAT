import yaml
import os
from typing import Dict


class AppConfig:
    """Configuration loader for MCAT application."""
    
    def __init__(self):
        self.config_dir = os.path.dirname(__file__)
        self.columns = self.load_columns()
        self.scraper_settings = self.load_scraper_settings()
    
    def load_columns(self) -> Dict:
        """Load column mappings from YAML file."""
        columns_path = os.path.join(self.config_dir, 'columns.yaml')
        try:
            with open(columns_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load columns.yaml: {e}")
    
    def load_scraper_settings(self) -> Dict:
        """Load scraper settings with defaults."""
        return {
            'timeout': 30,
            'max_workers': 10,
            'retry_count': 3,
            'headless': True
        }
    
    def get_platform_columns(self, platform: str) -> Dict[str, str]:
        """Get column mappings for a specific platform."""
        return self.columns.get(platform, {}).get('columns', {})
    
    def get_column_name(self, platform: str, column_type: str) -> str:
        """Get the column name for a specific platform and column type."""
        return self.get_platform_columns(platform).get(column_type, "")
    
    def get_supported_platforms(self) -> list:
        """Get list of supported platforms."""
        return list(self.columns.keys())


# Global config instance
config = AppConfig()