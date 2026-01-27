"""
Interrupted run dialog view - passive modal shown when opening a project with an interrupted run.

This view is completely passive following MVP pattern:
- Displays data provided by presenter
- Forwards all user actions to presenter via callbacks
- Holds no state
"""

import dearpygui.dearpygui as dpg
from typing import Callable, Optional


class InterruptedRunDialog:
    """
    Passive modal view for interrupted run decisions.

    All state is managed by the presenter. This view only:
    - Renders UI elements
    - Displays data when told
    - Forwards user interactions to callbacks
    """

    def __init__(self):
        self.modal_id = "interrupted_run_dialog"

        # UI element IDs
        self.message_text_id = "ird_message_text"
        self.details_text_id = "ird_details_text"

        # Callbacks (set by presenter)
        self._on_resume: Optional[Callable[[], None]] = None
        self._on_start_new: Optional[Callable[[], None]] = None

    def set_callbacks(
        self,
        on_resume: Callable[[], None],
        on_start_new: Callable[[], None]
    ) -> None:
        """Set all callback functions from presenter."""
        self._on_resume = on_resume
        self._on_start_new = on_start_new

    def setup_ui(self) -> None:
        """Create the dialog modal (hidden initially)."""
        with dpg.window(
            label="Interrupted Run Detected",
            modal=True,
            show=False,
            tag=self.modal_id,
            width=400,
            height=200,
            no_resize=True,
            no_close=True
        ):
            dpg.add_spacer(height=10)

            # Message
            dpg.add_text(
                "A previous run was interrupted.",
                tag=self.message_text_id,
                color=[255, 200, 100]
            )

            dpg.add_spacer(height=10)

            # Details
            dpg.add_text(
                "",
                tag=self.details_text_id,
                color=[180, 180, 180],
                wrap=380
            )

            dpg.add_spacer(height=20)

            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Resume Run",
                    width=150,
                    height=35,
                    callback=self._handle_resume
                )
                dpg.add_spacer(width=20)
                dpg.add_button(
                    label="Start New Run",
                    width=150,
                    height=35,
                    callback=self._handle_start_new
                )

    # === Display methods (called by presenter) ===

    def display_details(self, details_text: str) -> None:
        """Display run details."""
        dpg.set_value(self.details_text_id, details_text)

    def show(self) -> None:
        """Show the dialog."""
        dpg.show_item(self.modal_id)

    def hide(self) -> None:
        """Hide the dialog."""
        dpg.hide_item(self.modal_id)

    # === Internal event handlers (forward to presenter) ===

    def _handle_resume(self, sender, app_data) -> None:
        """Forward resume request to presenter."""
        self.hide()
        if self._on_resume:
            self._on_resume()

    def _handle_start_new(self, sender, app_data) -> None:
        """Forward start new request to presenter."""
        self.hide()
        if self._on_start_new:
            self._on_start_new()
