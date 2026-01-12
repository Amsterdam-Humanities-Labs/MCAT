"""
Console presenter implementing MVP pattern for global console.

Coordinates between ConsoleLogger service and ConsolePanel view.
"""

from typing import Optional
from utils.console_logger import ConsoleLogger


class ConsolePresenter:
    """Presenter for global console - coordinates logger service and console view."""

    def __init__(self, view, logger: ConsoleLogger):
        """
        Initialize console presenter.

        Args:
            view: ConsolePanel instance (the view component)
            logger: ConsoleLogger instance (the service)
        """
        self.view = view
        self.logger = logger

    def update(self):
        """
        Poll logger service for new messages and update view.

        This is the presenter's coordination logic - it gets data from
        the service and tells the view what to display.
        """
        messages = self.logger.get_messages()
        for message in messages:
            self.view.add_message(message)
