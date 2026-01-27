"""
Presenter layer for MCAT application implementing MVP pattern.

This module contains presenter classes that coordinate between the View (UI)
and Model (services) layers, providing clear separation of concerns and
improved testability.
"""

# Legacy presenters (to be removed in Phase 7)
from .base_tab_presenter import BaseTabPresenter
from .youtube_presenter import YouTubePresenter

# New project-based presenters
from .start_screen_presenter import StartScreenPresenter
from .new_project_presenter import NewProjectPresenter
from .project_presenter import ProjectPresenter

__all__ = [
    # Legacy
    'BaseTabPresenter',
    'YouTubePresenter',
    # New
    'StartScreenPresenter',
    'NewProjectPresenter',
    'ProjectPresenter',
]