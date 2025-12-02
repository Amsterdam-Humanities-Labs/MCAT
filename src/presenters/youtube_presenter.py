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
        YouTube-specific column suggestions.
        
        Looks for columns that are likely to contain YouTube video URLs
        based on common naming patterns.
        
        Args:
            file_info: Information about the loaded CSV file
        """
        # Get potential URL columns from the base service
        url_candidates = self.csv_service.get_url_column_candidates(file_info)
        
        # YouTube-specific patterns (in priority order)
        youtube_patterns = [
            'video',      # "video_url", "video_link"
            'youtube',    # "youtube_url", "youtube_link"
            'url',        # "url", "post_url"
            'link',       # "link", "video_link"
            'post'        # "post", "post_url"
        ]
        
        # Find best match based on patterns
        best_suggestion = None
        for pattern in youtube_patterns:
            for column in url_candidates:
                if pattern in column.lower():
                    best_suggestion = column
                    break
            if best_suggestion:
                break
        
        # Fall back to first URL candidate if no pattern matches
        if not best_suggestion and url_candidates:
            best_suggestion = url_candidates[0]
        
        # Suggest the best match to the view
        if best_suggestion:
            self.view.suggest_url_column(best_suggestion)
    
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
        Get suggested columns to preserve for YouTube analysis.
        
        Args:
            file_info: Information about the loaded CSV file
            
        Returns:
            List of column names that are commonly useful for YouTube analysis
        """
        if not file_info or not file_info.valid:
            return []
        
        # Common YouTube analysis columns
        useful_patterns = [
            'title',
            'description', 
            'channel',
            'view',
            'like',
            'comment',
            'date',
            'publish',
            'upload',
            'duration',
            'category',
            'tag'
        ]
        
        suggested = []
        for column in file_info.columns:
            column_lower = column.lower()
            if any(pattern in column_lower for pattern in useful_patterns):
                suggested.append(column)
        
        return suggested