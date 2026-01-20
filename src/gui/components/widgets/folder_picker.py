"""Folder selection component following MVP pattern."""

import dearpygui.dearpygui as dpg
from typing import Callable, Optional
import os


class FolderPicker:
    """Folder selection component for output directories."""

    def __init__(self, parent_window: str, callback: Optional[Callable] = None, id_suffix: str = ""):
        """
        Initialize folder picker.

        Args:
            parent_window: Parent DearPyGUI window ID
            callback: Callback function called when folder is selected
            id_suffix: Unique suffix for widget IDs
        """
        self.parent_window = parent_window
        self.callback = callback
        self.selected_folder = ""
        self.id_suffix = id_suffix
        self.folder_dialog_id = f"folder_dialog{id_suffix}"
        self.folder_input_id = f"folder_input{id_suffix}"
        self.browse_button_id = f"browse_folder_button{id_suffix}"

    def setup_ui(self, input_width: int = 400, placeholder_text: str = "No folder selected", label: str = None):
        """
        Create the folder picker UI components.

        Args:
            input_width: Width of the input text field
            placeholder_text: Placeholder text when no folder selected
            label: Optional label above the picker
        """
        with dpg.group(parent=self.parent_window):
            # Optional label above folder picker
            if label:
                dpg.add_text(label, color=[255, 255, 255])

            with dpg.group(horizontal=True):
                # Folder path input (read-only display)
                dpg.add_input_text(
                    tag=self.folder_input_id,
                    default_value=placeholder_text,
                    width=input_width,
                    readonly=True,
                    hint="Selected output folder path will appear here"
                )

                # Browse button
                dpg.add_button(
                    tag=self.browse_button_id,
                    label="Browse",
                    callback=self._show_folder_dialog
                )

        # Folder dialog (hidden by default)
        with dpg.file_dialog(
            tag=self.folder_dialog_id,
            directory_selector=True,  # Key difference: select directories
            show=False,
            callback=self._folder_selected,
            cancel_callback=self._folder_dialog_cancelled,
            width=700,
            height=400,
            modal=True
        ):
            pass  # No file extensions for directory selector

    def _show_folder_dialog(self, *args, **kwargs):
        """Show the folder selection dialog."""
        dpg.show_item(self.folder_dialog_id)

    def _folder_selected(self, sender, app_data, *args, **kwargs):
        """Handle folder selection from dialog."""
        folder_path = app_data['file_path_name']
        self.selected_folder = folder_path

        # Update the display
        display_path = self._get_display_path(folder_path)
        dpg.set_value(self.folder_input_id, display_path)

        # Call the callback if provided
        if self.callback:
            try:
                self.callback(folder_path)
            except Exception as e:
                print(f"Error in folder picker callback: {e}")

    def _folder_dialog_cancelled(self):
        """Handle folder dialog cancellation."""
        pass  # Do nothing when cancelled

    def _get_display_path(self, full_path: str) -> str:
        """
        Get a display-friendly path (truncate if too long).

        Args:
            full_path: Full folder path

        Returns:
            Truncated path for display
        """
        if len(full_path) <= 60:
            return full_path

        # Show last two directories
        parts = full_path.split(os.sep)
        if len(parts) >= 2:
            return f".../{parts[-2]}/{parts[-1]}"
        return full_path

    def get_selected_folder(self) -> str:
        """
        Get the currently selected folder path.

        Returns:
            Selected folder path or empty string
        """
        return self.selected_folder

    def set_folder(self, folder_path: str):
        """
        Set the folder path programmatically.

        Args:
            folder_path: Folder path to set
        """
        self.selected_folder = folder_path
        display_path = self._get_display_path(folder_path)
        if dpg.does_item_exist(self.folder_input_id):
            dpg.set_value(self.folder_input_id, display_path)

    def clear_selection(self):
        """Clear the current folder selection."""
        self.selected_folder = ""
        if dpg.does_item_exist(self.folder_input_id):
            dpg.set_value(self.folder_input_id, "No folder selected")

    def set_enabled(self, enabled: bool):
        """
        Enable or disable the folder picker.

        Args:
            enabled: Whether to enable the picker
        """
        if dpg.does_item_exist(self.browse_button_id):
            dpg.configure_item(self.browse_button_id, enabled=enabled)
