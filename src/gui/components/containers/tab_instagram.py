"""
Instagram-specific tab implementing MVP pattern.

This tab extends BaseTab to provide Instagram-specific behavior while
delegating all business logic to the InstagramPresenter.
"""

from .base_tab import BaseTab
from presenters.instagram_presenter import InstagramPresenter


class InstagramTab(BaseTab):
    """Instagram-specific tab implementing MVP pattern with BaseTab."""

    def __init__(self, parent_window: str, processing_controller=None, state_manager=None):
        """
        Initialize Instagram tab.

        Args:
            parent_window: Parent DearPyGUI window ID
            processing_controller: Legacy parameter (not used in MVP)
            state_manager: Legacy parameter (not used in MVP)
        """
        super().__init__(parent_window, platform="instagram")

    def _create_presenter(self):
        """Create Instagram-specific presenter."""
        return InstagramPresenter(self)

    def get_platform_display_name(self) -> str:
        """Get Instagram platform display name."""
        return "Instagram"
