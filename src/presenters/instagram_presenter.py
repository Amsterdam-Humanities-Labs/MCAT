"""
Instagram-specific presenter implementing platform-specific behavior.
"""

from typing import Dict, Any
from .base_tab_presenter import BaseTabPresenter
from models.file_models import FileInfo


class InstagramPresenter(BaseTabPresenter):
    """Instagram-specific presenter logic."""

    def __init__(self, view):
        """
        Initialize Instagram presenter.

        Args:
            view: The Instagram tab view component
        """
        super().__init__(view, platform="instagram")

    def _suggest_columns(self, file_info: FileInfo):
        """
        No column suggestions - let users choose themselves.

        Args:
            file_info: Information about the loaded CSV file
        """
        pass

    def _get_platform_validation_rules(self) -> Dict[str, Any]:
        """
        Instagram-specific validation rules.

        Returns:
            Dictionary containing Instagram-specific validation settings
        """
        return {
            'required_url_patterns': [
                'instagram.com'
            ],
            'min_url_length': 10,
            'max_batch_size': 500,  # Instagram rate limiting is stricter
            'suggested_delay': 2.5   # Seconds between requests
        }

    def get_platform_display_name(self) -> str:
        """
        Get Instagram platform display name.

        Returns:
            Human-readable platform name for UI display
        """
        return "Instagram"

    def validate_url_format(self, url: str) -> bool:
        """
        Validate that a URL is a valid Instagram URL format.

        Args:
            url: URL string to validate

        Returns:
            True if URL appears to be an Instagram URL
        """
        if not url or len(url) < 10:
            return False

        url_lower = url.lower()
        return 'instagram.com' in url_lower

    def extract_post_id(self, url: str) -> str:
        """
        Extract post ID from Instagram URL.

        Args:
            url: Instagram URL

        Returns:
            Post ID string, or empty string if not found
        """
        try:
            # Handle various Instagram URL formats:
            # https://www.instagram.com/p/ABC123/
            # https://www.instagram.com/reel/ABC123/
            # https://www.instagram.com/tv/ABC123/
            parts = url.rstrip('/').split('/')
            for i, part in enumerate(parts):
                if part in ('p', 'reel', 'tv') and i + 1 < len(parts):
                    return parts[i + 1]
            return ""
        except Exception:
            return ""

    def get_suggested_preserve_columns(self, file_info: FileInfo) -> list:
        """
        No column suggestions - let users choose themselves.

        Args:
            file_info: Information about the loaded CSV file

        Returns:
            Empty list - no automatic suggestions
        """
        return []
