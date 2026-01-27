"""
Navigation state model for screen management.

Tracks which screen is currently active in the application.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, List


class Screen(Enum):
    """Available screens in the application."""
    START = "start"
    NEW_PROJECT = "new_project"
    PROJECT = "project"


@dataclass
class NavigationState:
    """
    Model representing the current navigation state.

    Holds the active screen and notifies observers on changes.
    """

    _current_screen: Screen = field(default=Screen.START)
    _observers: List[Callable[[Screen, Screen], None]] = field(default_factory=list)

    @property
    def current_screen(self) -> Screen:
        """Get the current active screen."""
        return self._current_screen

    def navigate_to(self, screen: Screen) -> None:
        """
        Navigate to a new screen.

        Args:
            screen: The screen to navigate to
        """
        if screen == self._current_screen:
            return

        previous = self._current_screen
        self._current_screen = screen
        self._notify_observers(previous, screen)

    def add_observer(self, callback: Callable[[Screen, Screen], None]) -> None:
        """
        Add an observer to be notified of navigation changes.

        Args:
            callback: Function called with (previous_screen, new_screen)
        """
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[Screen, Screen], None]) -> None:
        """Remove an observer."""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self, previous: Screen, current: Screen) -> None:
        """Notify all observers of a navigation change."""
        for observer in self._observers:
            observer(previous, current)
