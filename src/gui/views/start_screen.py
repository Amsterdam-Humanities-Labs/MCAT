"""
Start screen view - the initial screen shown when the app launches.

Provides options to create a new project or open an existing one.
Displayed as a centered card with white border.
"""

import dearpygui.dearpygui as dpg
from typing import Callable, Optional


# Card dimensions
CARD_WIDTH = 400
CARD_HEIGHT = 350


class StartScreen:
    """
    Start screen view shown when no project is open.

    Provides buttons to create a new project or open an existing one.
    Displayed as a centered bordered card that stays centered on resize.
    """

    def __init__(self):
        self.container_id = "start_screen"
        self.card_id = "start_screen_card"
        self.presenter: Optional[object] = None

        # Callbacks
        self._on_new_project: Optional[Callable] = None
        self._on_open_project: Optional[Callable] = None

    def set_presenter(self, presenter) -> None:
        """Set the presenter for this view."""
        self.presenter = presenter

    def set_callbacks(
        self,
        on_new_project: Callable,
        on_open_project: Callable
    ) -> None:
        """
        Set callback functions for user actions.

        Args:
            on_new_project: Called when user clicks "New Project"
            on_open_project: Called when user clicks "Open Project"
        """
        self._on_new_project = on_new_project
        self._on_open_project = on_open_project

    def setup_ui(self, parent: str) -> None:
        """
        Create the start screen UI.

        Args:
            parent: Parent window/container ID
        """
        with dpg.group(tag=self.container_id, parent=parent):
            # Bordered card container - positioned absolutely
            with dpg.child_window(
                tag=self.card_id,
                width=CARD_WIDTH,
                height=CARD_HEIGHT,
                border=True,
                no_scrollbar=True
            ):
                # Apply white border theme
                self._apply_card_theme()

                # Card content with padding
                dpg.add_spacer(height=40)

                # Centered content inside card
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=75)

                    with dpg.group():
                        # Title
                        dpg.add_text(
                            "MCAT",
                            color=[255, 255, 255]
                        )
                        dpg.add_text(
                            "Moderation Content Analysis Tool",
                            color=[180, 180, 180]
                        )

                        dpg.add_spacer(height=40)

                        # Buttons
                        dpg.add_button(
                            label="New Project",
                            width=250,
                            height=40,
                            callback=self._handle_new_project
                        )

                        dpg.add_spacer(height=10)

                        dpg.add_button(
                            label="Open Project",
                            width=250,
                            height=40,
                            callback=self._handle_open_project
                        )

                        dpg.add_spacer(height=40)

                        # Version info
                        dpg.add_text(
                            "v0.2.0 - Project-based workflow",
                            color=[120, 120, 120]
                        )

        # Register resize handler for centering
        with dpg.item_handler_registry(tag="start_screen_resize_handler"):
            dpg.add_item_visible_handler(callback=self._center_card)

        dpg.bind_item_handler_registry(self.container_id, "start_screen_resize_handler")

        # Initial centering
        self._center_card()

    def _apply_card_theme(self) -> None:
        """Apply white border theme to the card."""
        with dpg.theme() as card_theme:
            with dpg.theme_component(dpg.mvChildWindow):
                # White/light border
                dpg.add_theme_color(dpg.mvThemeCol_Border, [200, 200, 200, 255])
                dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
                # Slightly lighter background for the card
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, [40, 35, 30, 255])

        dpg.bind_item_theme(self.card_id, card_theme)

    def _center_card(self, sender=None, app_data=None) -> None:
        """Center the card in the viewport."""
        if not dpg.does_item_exist(self.card_id):
            return

        # Get viewport dimensions
        viewport_width = dpg.get_viewport_client_width()
        viewport_height = dpg.get_viewport_client_height()

        # Calculate centered position
        x = (viewport_width - CARD_WIDTH) // 2
        y = (viewport_height - CARD_HEIGHT) // 2

        # Apply position
        dpg.set_item_pos(self.card_id, [x, y])

    def _handle_new_project(self, sender, app_data) -> None:
        """Handle New Project button click."""
        if self._on_new_project:
            self._on_new_project()

    def _handle_open_project(self, sender, app_data) -> None:
        """Handle Open Project button click."""
        if self._on_open_project:
            self._on_open_project()

    def show(self) -> None:
        """Show the start screen."""
        if dpg.does_item_exist(self.container_id):
            dpg.show_item(self.container_id)
            self._center_card()

    def hide(self) -> None:
        """Hide the start screen."""
        if dpg.does_item_exist(self.container_id):
            dpg.hide_item(self.container_id)

    def cleanup(self) -> None:
        """Clean up resources."""
        if dpg.does_item_exist("start_screen_resize_handler"):
            dpg.delete_item("start_screen_resize_handler")
        if dpg.does_item_exist(self.container_id):
            dpg.delete_item(self.container_id)
