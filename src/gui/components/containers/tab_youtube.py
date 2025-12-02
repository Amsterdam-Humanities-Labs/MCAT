"""
YouTube-specific tab implementing MVP pattern.

This tab extends BaseTab to provide YouTube-specific behavior while 
delegating all business logic to the YouTubePresenter.
"""

from .base_tab import BaseTab
from presenters.youtube_presenter import YouTubePresenter


class YouTubeTab(BaseTab):
    """YouTube-specific tab implementing MVP pattern with BaseTab."""
    
    def __init__(self, parent_window: str, processing_controller=None, state_manager=None):
        """
        Initialize YouTube tab.
        
        Args:
            parent_window: Parent DearPyGUI window ID
            processing_controller: Legacy parameter (not used in MVP)
            state_manager: Legacy parameter (not used in MVP)
        """
        # Initialize base tab with YouTube platform
        super().__init__(parent_window, platform="youtube")
    
    def _create_presenter(self):
        """Create YouTube-specific presenter."""
        return YouTubePresenter(self)
    
    def get_platform_display_name(self) -> str:
        """Get YouTube platform display name."""
        return "YouTube"
    
    # YouTube-specific UI customizations (if any)
    # Currently all behavior is handled by BaseTab and YouTubePresenter
    # This class is intentionally minimal to demonstrate the MVP pattern
    
    # Example of platform-specific UI customization (uncomment if needed):
    # def _setup_processing_section(self):
    #     """YouTube-specific processing section setup."""
    #     super()._setup_processing_section()
    #     # Add YouTube-specific UI elements here if needed