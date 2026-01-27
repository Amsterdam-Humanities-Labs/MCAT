"""
Add URLs dialog view - passive modal for importing URLs into a project.

This view is completely passive following MVP pattern:
- Displays data provided by presenter
- Forwards all user actions to presenter via callbacks
- Holds no state
"""

import dearpygui.dearpygui as dpg
from typing import Callable, Optional


class AddUrlsDialog:
    """
    Passive modal view for adding URLs to a project.

    All state is managed by the presenter. This view only:
    - Renders UI elements
    - Displays data when told
    - Forwards user interactions to callbacks
    """

    def __init__(self):
        self.modal_id = "add_urls_dialog"

        # UI element IDs
        self.csv_text_id = "aud_csv_text"
        self.preview_text_id = "aud_preview_text"
        self.import_btn_id = "aud_import_btn"
        self.error_text_id = "aud_error_text"

        # Callbacks (set by presenter)
        self._on_browse_csv: Optional[Callable[[], None]] = None
        self._on_import: Optional[Callable[[], None]] = None
        self._on_cancel: Optional[Callable[[], None]] = None

    def set_callbacks(
        self,
        on_browse_csv: Callable[[], None],
        on_import: Callable[[], None],
        on_cancel: Callable[[], None]
    ) -> None:
        """Set all callback functions from presenter."""
        self._on_browse_csv = on_browse_csv
        self._on_import = on_import
        self._on_cancel = on_cancel

    def setup_ui(self) -> None:
        """Create the dialog modal (hidden initially)."""
        with dpg.window(
            label="Add URLs",
            modal=True,
            show=False,
            tag=self.modal_id,
            width=450,
            height=250,
            no_resize=True
        ):
            # Error message (hidden by default)
            dpg.add_text(
                "",
                tag=self.error_text_id,
                color=[255, 100, 100],
                show=False
            )

            dpg.add_spacer(height=10)

            # CSV file selection
            dpg.add_text("Select CSV file with URLs to import:")

            dpg.add_spacer(height=5)

            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag=self.csv_text_id,
                    width=320,
                    readonly=True,
                    hint="Select CSV file..."
                )
                dpg.add_button(
                    label="Browse",
                    callback=self._handle_browse_csv
                )

            dpg.add_spacer(height=15)

            # Preview area
            dpg.add_text(
                "",
                tag=self.preview_text_id,
                color=[180, 180, 180],
                wrap=400
            )

            dpg.add_spacer(height=20)

            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Cancel",
                    width=100,
                    callback=self._handle_cancel
                )
                dpg.add_spacer(width=150)
                dpg.add_button(
                    label="Import",
                    tag=self.import_btn_id,
                    width=100,
                    callback=self._handle_import,
                    enabled=False
                )

    # === Display methods (called by presenter) ===

    def display_csv_path(self, path: str) -> None:
        """Display selected CSV path."""
        dpg.set_value(self.csv_text_id, path)

    def display_preview(self, summary: str) -> None:
        """Display import preview summary."""
        dpg.set_value(self.preview_text_id, summary)

    def display_error(self, message: str) -> None:
        """Display error message."""
        dpg.set_value(self.error_text_id, message)
        dpg.show_item(self.error_text_id)

    def hide_error(self) -> None:
        """Hide error message."""
        dpg.hide_item(self.error_text_id)

    def set_import_enabled(self, enabled: bool) -> None:
        """Enable or disable the import button."""
        if enabled:
            dpg.enable_item(self.import_btn_id)
        else:
            dpg.disable_item(self.import_btn_id)

    def reset(self) -> None:
        """Reset the dialog to initial state."""
        dpg.set_value(self.csv_text_id, "")
        dpg.set_value(self.preview_text_id, "")
        dpg.disable_item(self.import_btn_id)
        self.hide_error()

    def show(self) -> None:
        """Show the dialog."""
        dpg.show_item(self.modal_id)

    def hide(self) -> None:
        """Hide the dialog."""
        dpg.hide_item(self.modal_id)

    # === Internal event handlers (forward to presenter) ===

    def _handle_browse_csv(self, sender, app_data) -> None:
        """Forward browse CSV request to presenter."""
        if self._on_browse_csv:
            self._on_browse_csv()

    def _handle_import(self, sender, app_data) -> None:
        """Forward import request to presenter."""
        if self._on_import:
            self._on_import()

    def _handle_cancel(self, sender, app_data) -> None:
        """Forward cancel request to presenter."""
        self.hide()
        if self._on_cancel:
            self._on_cancel()
