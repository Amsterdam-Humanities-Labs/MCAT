"""
New project wizard view - passive UI for creating a new project.

This view is completely passive following MVP pattern:
- Displays data provided by presenter
- Forwards all user actions to presenter via callbacks
- Holds no state

Displayed as a centered card with white border.
"""

import dearpygui.dearpygui as dpg
from pathlib import Path
from typing import Callable, Optional, List


# Card dimensions
CARD_WIDTH = 550
CARD_HEIGHT = 480


class NewProjectWizard:
    """
    Passive view for new project wizard.

    All state is managed by the presenter. This view only:
    - Renders UI elements
    - Displays data when told
    - Forwards user interactions to callbacks

    Displayed as a centered bordered card.
    """

    PLATFORMS = ["youtube", "instagram"]

    def __init__(self):
        self.container_id = "new_project_wizard"
        self.card_id = "new_project_card"

        # UI element IDs
        self.name_input_id = "npw_name_input"
        self.platform_combo_id = "npw_platform_combo"
        self.location_text_id = "npw_location_text"
        self.csv_text_id = "npw_csv_text"
        self.url_column_combo_id = "npw_url_column"
        self.preserve_group_id = "npw_preserve_group"
        self.error_text_id = "npw_error_text"
        self.step1_group_id = "npw_step1"
        self.step2_group_id = "npw_step2"
        self.back_btn_id = "npw_back_btn"
        self.next_btn_id = "npw_next_btn"

        # Callbacks (set by presenter)
        self._on_name_changed: Optional[Callable[[str], None]] = None
        self._on_platform_changed: Optional[Callable[[str], None]] = None
        self._on_browse_location: Optional[Callable[[], None]] = None
        self._on_browse_csv: Optional[Callable[[], None]] = None
        self._on_url_column_changed: Optional[Callable[[str], None]] = None
        self._on_preserve_column_toggled: Optional[Callable[[str, bool], None]] = None
        self._on_next: Optional[Callable[[], None]] = None
        self._on_back: Optional[Callable[[], None]] = None
        self._on_cancel: Optional[Callable[[], None]] = None

    def set_callbacks(
        self,
        on_name_changed: Callable[[str], None],
        on_platform_changed: Callable[[str], None],
        on_browse_location: Callable[[], None],
        on_browse_csv: Callable[[], None],
        on_url_column_changed: Callable[[str], None],
        on_preserve_column_toggled: Callable[[str, bool], None],
        on_next: Callable[[], None],
        on_back: Callable[[], None],
        on_cancel: Callable[[], None]
    ) -> None:
        """Set all callback functions from presenter."""
        self._on_name_changed = on_name_changed
        self._on_platform_changed = on_platform_changed
        self._on_browse_location = on_browse_location
        self._on_browse_csv = on_browse_csv
        self._on_url_column_changed = on_url_column_changed
        self._on_preserve_column_toggled = on_preserve_column_toggled
        self._on_next = on_next
        self._on_back = on_back
        self._on_cancel = on_cancel

    def setup_ui(self, parent: str) -> None:
        """Create the wizard view UI (hidden initially)."""
        with dpg.group(tag=self.container_id, parent=parent, show=False):
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
                dpg.add_spacer(height=20)

                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=25)

                    with dpg.group(width=CARD_WIDTH - 50):
                        # Header
                        dpg.add_text("New Project", color=[255, 255, 255])

                        dpg.add_spacer(height=10)

                        # Error message area (hidden by default)
                        dpg.add_text(
                            "",
                            tag=self.error_text_id,
                            color=[255, 100, 100],
                            show=False
                        )

                        dpg.add_spacer(height=10)

                        # Step 1: Project basics
                        with dpg.group(tag=self.step1_group_id, show=True):
                            dpg.add_text("Step 1: Project Basics", color=[200, 200, 200])
                            dpg.add_separator()
                            dpg.add_spacer(height=10)

                            # Project name
                            dpg.add_text("Project Name:")
                            dpg.add_input_text(
                                tag=self.name_input_id,
                                width=480,
                                hint="My Research Project",
                                callback=self._handle_name_changed
                            )

                            dpg.add_spacer(height=10)

                            # Platform
                            dpg.add_text("Platform:")
                            dpg.add_combo(
                                items=self.PLATFORMS,
                                tag=self.platform_combo_id,
                                default_value=self.PLATFORMS[0],
                                width=480,
                                callback=self._handle_platform_changed
                            )

                            dpg.add_spacer(height=10)

                            # Project location
                            dpg.add_text("Project Location:")
                            with dpg.group(horizontal=True):
                                dpg.add_input_text(
                                    tag=self.location_text_id,
                                    width=390,
                                    readonly=True,
                                    hint="Select folder..."
                                )
                                dpg.add_button(
                                    label="Browse",
                                    callback=self._handle_browse_location
                                )

                            dpg.add_spacer(height=10)

                            # Source CSV
                            dpg.add_text("Source CSV:")
                            with dpg.group(horizontal=True):
                                dpg.add_input_text(
                                    tag=self.csv_text_id,
                                    width=390,
                                    readonly=True,
                                    hint="Select CSV file..."
                                )
                                dpg.add_button(
                                    label="Browse",
                                    callback=self._handle_browse_csv
                                )

                        # Step 2: Column mapping
                        with dpg.group(tag=self.step2_group_id, show=False):
                            dpg.add_text("Step 2: Column Mapping", color=[200, 200, 200])
                            dpg.add_separator()
                            dpg.add_spacer(height=10)

                            # URL column
                            dpg.add_text("URL Column:")
                            dpg.add_combo(
                                items=[],
                                tag=self.url_column_combo_id,
                                width=480,
                                callback=self._handle_url_column_changed
                            )

                            dpg.add_spacer(height=10)

                            # Preserve columns
                            dpg.add_text("Preserve Columns (optional):")
                            with dpg.child_window(height=150, border=True):
                                with dpg.group(tag=self.preserve_group_id):
                                    pass  # Checkboxes added dynamically

                        dpg.add_spacer(height=20)

                        # Navigation buttons
                        with dpg.group(horizontal=True):
                            dpg.add_button(
                                label="Cancel",
                                width=100,
                                callback=self._handle_cancel
                            )
                            dpg.add_spacer(width=280)
                            dpg.add_button(
                                label="Back",
                                width=80,
                                callback=self._handle_back,
                                tag=self.back_btn_id,
                                show=False
                            )
                            dpg.add_button(
                                label="Next",
                                width=80,
                                callback=self._handle_next,
                                tag=self.next_btn_id
                            )

        # Register resize handler for centering
        with dpg.item_handler_registry(tag="new_project_resize_handler"):
            dpg.add_item_visible_handler(callback=self._center_card)

        dpg.bind_item_handler_registry(self.container_id, "new_project_resize_handler")

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

    # === Display methods (called by presenter) ===

    def display_step(self, step: int) -> None:
        """Display the specified step."""
        if step == 1:
            dpg.show_item(self.step1_group_id)
            dpg.hide_item(self.step2_group_id)
            dpg.hide_item(self.back_btn_id)
            dpg.configure_item(self.next_btn_id, label="Next")
        elif step == 2:
            dpg.hide_item(self.step1_group_id)
            dpg.show_item(self.step2_group_id)
            dpg.show_item(self.back_btn_id)
            dpg.configure_item(self.next_btn_id, label="Create")

    def display_name(self, name: str) -> None:
        """Display project name."""
        dpg.set_value(self.name_input_id, name)

    def display_platform(self, platform: str) -> None:
        """Display selected platform."""
        dpg.set_value(self.platform_combo_id, platform)

    def display_location(self, path: str) -> None:
        """Display selected location path."""
        dpg.set_value(self.location_text_id, path)

    def display_csv_path(self, path: str) -> None:
        """Display selected CSV path."""
        dpg.set_value(self.csv_text_id, path)

    def display_columns(self, columns: List[str], selected_url_column: str = "") -> None:
        """Display available columns in URL column combo."""
        dpg.configure_item(self.url_column_combo_id, items=columns)
        if selected_url_column:
            dpg.set_value(self.url_column_combo_id, selected_url_column)

    def display_preserve_columns(self, columns: List[str], url_column: str, selected: List[str]) -> None:
        """Display preserve column checkboxes."""
        # Clear existing checkboxes
        if dpg.does_item_exist(self.preserve_group_id):
            dpg.delete_item(self.preserve_group_id, children_only=True)

        # Create checkboxes for each column except URL column
        for col in columns:
            if col != url_column:
                cb_id = f"npw_preserve_{col}"
                dpg.add_checkbox(
                    label=col,
                    tag=cb_id,
                    default_value=(col in selected),
                    parent=self.preserve_group_id,
                    callback=lambda s, a, c=col: self._handle_preserve_toggled(c)
                )

    def display_error(self, message: str) -> None:
        """Display error message."""
        dpg.set_value(self.error_text_id, message)
        dpg.show_item(self.error_text_id)

    def hide_error(self) -> None:
        """Hide error message."""
        dpg.hide_item(self.error_text_id)

    def show(self) -> None:
        """Show the wizard view."""
        dpg.show_item(self.container_id)
        self._center_card()

    def hide(self) -> None:
        """Hide the wizard view."""
        dpg.hide_item(self.container_id)

    def cleanup(self) -> None:
        """Clean up resources."""
        if dpg.does_item_exist("new_project_resize_handler"):
            dpg.delete_item("new_project_resize_handler")
        if dpg.does_item_exist(self.container_id):
            dpg.delete_item(self.container_id)

    # === Input getters (for presenter to read current values) ===

    def get_name(self) -> str:
        """Get current name input value."""
        return dpg.get_value(self.name_input_id)

    def get_platform(self) -> str:
        """Get current platform selection."""
        return dpg.get_value(self.platform_combo_id)

    def get_url_column(self) -> str:
        """Get current URL column selection."""
        return dpg.get_value(self.url_column_combo_id)

    # === Internal event handlers (forward to presenter) ===

    def _handle_name_changed(self, sender, app_data) -> None:
        """Forward name change to presenter."""
        if self._on_name_changed:
            self._on_name_changed(app_data)

    def _handle_platform_changed(self, sender, app_data) -> None:
        """Forward platform change to presenter."""
        if self._on_platform_changed:
            self._on_platform_changed(app_data)

    def _handle_browse_location(self, sender, app_data) -> None:
        """Forward browse location request to presenter."""
        if self._on_browse_location:
            self._on_browse_location()

    def _handle_browse_csv(self, sender, app_data) -> None:
        """Forward browse CSV request to presenter."""
        if self._on_browse_csv:
            self._on_browse_csv()

    def _handle_url_column_changed(self, sender, app_data) -> None:
        """Forward URL column change to presenter."""
        if self._on_url_column_changed:
            self._on_url_column_changed(app_data)

    def _handle_preserve_toggled(self, column: str) -> None:
        """Forward preserve column toggle to presenter."""
        if self._on_preserve_column_toggled:
            cb_id = f"npw_preserve_{column}"
            is_checked = dpg.get_value(cb_id)
            self._on_preserve_column_toggled(column, is_checked)

    def _handle_next(self, sender, app_data) -> None:
        """Forward next button click to presenter."""
        if self._on_next:
            self._on_next()

    def _handle_back(self, sender, app_data) -> None:
        """Forward back button click to presenter."""
        if self._on_back:
            self._on_back()

    def _handle_cancel(self, sender, app_data) -> None:
        """Forward cancel button click to presenter."""
        if self._on_cancel:
            self._on_cancel()
