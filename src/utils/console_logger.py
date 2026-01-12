"""
Console logger that redirects stdout to capture print statements.

This logger captures all print() statements while still displaying them
in the terminal, making them available for the GUI console component.
"""

import sys
from queue import Queue, Empty
from typing import Optional, Callable


class ConsoleLogger:
    """Redirects stdout to capture print statements while still showing them in terminal."""

    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the console logger.

        Args:
            callback: Optional callback function for each message
        """
        self.callback = callback
        self.original_stdout = sys.stdout
        self.message_queue = Queue(maxsize=1000)

    def write(self, message: str):
        """
        Write message to stdout and queue it for UI display.

        Args:
            message: Message to write
        """
        # Write to original stdout (terminal)
        self.original_stdout.write(message)

        # Queue message for UI (skip empty messages and newlines only)
        if message.strip():
            try:
                self.message_queue.put_nowait(message.strip())
            except:
                pass  # Queue full, drop message

    def flush(self):
        """Flush the output stream."""
        self.original_stdout.flush()

    def get_messages(self) -> list:
        """
        Get all queued messages (non-blocking).

        Returns:
            List of messages from the queue
        """
        messages = []
        while True:
            try:
                msg = self.message_queue.get_nowait()
                messages.append(msg)
            except Empty:
                break
        return messages

    def install(self):
        """Start capturing stdout."""
        sys.stdout = self

    def uninstall(self):
        """Stop capturing stdout and restore original."""
        sys.stdout = self.original_stdout
