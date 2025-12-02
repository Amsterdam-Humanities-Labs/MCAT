"""
Presenter layer for MCAT application implementing MVP pattern.

This module contains presenter classes that coordinate between the View (UI) 
and Model (services) layers, providing clear separation of concerns and 
improved testability.
"""

from .base_tab_presenter import BaseTabPresenter
from .youtube_presenter import YouTubePresenter

__all__ = [
    'BaseTabPresenter',
    'YouTubePresenter'
]