"""
YouTube-specific presenter implementing platform-specific behavior.
"""

from typing import Dict, Any
from .base_tab_presenter import BaseTabPresenter
from models.file_models import FileInfo


class YouTubePresenter(BaseTabPresenter):
    """YouTube-specific presenter logic."""
    
    def __init__(self, view):
        """
        Initialize YouTube presenter.
        
        Args:
            view: The YouTube tab view component
        """
        super().__init__(view, platform="youtube")
    
    def _suggest_columns(self, file_info: FileInfo):
        """
        No column suggestions - let users choose themselves.

        Args:
            file_info: Information about the loaded CSV file
        """
        # Intentionally empty - no automatic suggestions
        pass

    def _get_platform_validation_rules(self) -> Dict[str, Any]:
        """
        YouTube-specific validation rules.
        
        Returns:
            Dictionary containing YouTube-specific validation settings
        """
        return {
            'required_url_patterns': [
                'youtube.com',
                'youtu.be'
            ],
            'min_url_length': 10,
            'max_batch_size': 1000,  # YouTube rate limiting considerations
            'suggested_delay': 2.0   # Seconds between requests
        }
    
    def get_platform_display_name(self) -> str:
        """
        Get YouTube platform display name.
        
        Returns:
            Human-readable platform name for UI display
        """
        return "YouTube"
    
    def validate_url_format(self, url: str) -> bool:
        """
        Validate that a URL is a valid YouTube URL format.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if URL appears to be a YouTube URL
        """
        if not url or len(url) < 10:
            return False
        
        # Check for YouTube domain patterns
        youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
        url_lower = url.lower()
        
        return any(domain in url_lower for domain in youtube_domains)
    
    def extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID string, or empty string if not found
        """
        import re
        
        # Pattern for extracting YouTube video ID
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
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
