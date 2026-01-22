"""
Console panel component for displaying debug messages and logs.

This component displays captured print statements, errors, and other
messages in a scrollable window with color-coded output.
"""

import dearpygui.dearpygui as dpg
from collections import deque
from typing import Optional

from gui.themes.noctua_theme import create_dark_container_theme


class ConsolePanel:
    """Console panel for displaying debug messages and logs."""

    def __init__(self, parent_window: str, platform: str = "global"):
        """
        Initialize the console panel.

        Args:
            parent_window: Parent window ID for the console
            platform: Platform identifier (default "global" for global console)
        """
        self.parent_window = parent_window
        self.platform = platform

        # UI element IDs (uses platform prefix)
        self.container_id = f"console_container_{platform}"
        self.scroll_id = f"console_scroll_{platform}"
        self.content_id = f"console_content_{platform}"

        # Message buffer (max 500 messages)
        self.messages = deque(maxlen=500)
        self.message_count = 0

    def setup_ui(self):
        """Create the console UI."""
        with dpg.group(tag=self.container_id, parent=self.parent_window):
            # Console header
            dpg.add_text("Console Output", color=[255, 255, 255])
            dpg.add_spacer(height=5)

            # Scrollable console area
            with dpg.child_window(
                tag=self.scroll_id,
                height=200,
                border=True,
                horizontal_scrollbar=False
            ):
                # Content group (messages added here)
                with dpg.group(tag=self.content_id):
                    pass  # Start empty, messages will appear as they come

            # Apply dark theme to console background
            dpg.bind_item_theme(self.scroll_id, create_dark_container_theme())

    def add_message(self, message: str):
        """
        Add a message to the console.

        Args:
            message: Message text to display
        """
        # Add to buffer
        self.messages.append(message)
        self.message_count += 1

        # Determine color based on content
        color = self._get_message_color(message)

        # Add to UI (if content exists)
        if dpg.does_item_exist(self.content_id):
            # Add text with timestamp-like prefix
            dpg.add_text(f"[{self.message_count}] {message}",
                        color=color,
                        parent=self.content_id,
                        wrap=600)  # Wrap long lines

            # Auto-scroll to bottom
            self._scroll_to_bottom()

    def _get_message_color(self, message: str) -> list:
        """
        Get color based on message content.

        Args:
            message: Message text to analyze

        Returns:
            RGB color list [R, G, B]
        """
        msg_lower = message.lower()

        # Error messages (red)
        if any(word in msg_lower for word in ['error', 'exception', 'failed', 'traceback', '❌']):
            return [255, 100, 100]

        # Warning messages (orange)
        if any(word in msg_lower for word in ['warning', 'warn', '⚠']):
            return [255, 200, 100]

        # Success messages (green)
        if any(word in msg_lower for word in ['success', 'completed', '✅']):
            return [100, 255, 100]

        # Info messages (light gray)
        return [180, 180, 180]

    def _scroll_to_bottom(self):
        """Scroll console to bottom to show latest message."""
        if dpg.does_item_exist(self.scroll_id):
            # Set scroll position to max
            dpg.set_y_scroll(self.scroll_id, -1.0)

    def clear(self):
        """Clear all console messages."""
        self.messages.clear()
        self.message_count = 0

        if dpg.does_item_exist(self.content_id):
            dpg.delete_item(self.content_id, children_only=True)
            dpg.add_text("Console cleared.", color=[120, 120, 120], parent=self.content_id)
