import dearpygui.dearpygui as dpg
from typing import Callable, Optional
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))


class FilePicker:
    """File selection component for CSV files."""
    
    def __init__(self, parent_window: str, callback: Optional[Callable] = None, id_suffix: str = ""):
        self.parent_window = parent_window
        self.callback = callback
        self.selected_file = ""
        self.id_suffix = id_suffix
        self.file_dialog_id = f"file_dialog{id_suffix}"
        self.file_input_id = f"file_input{id_suffix}"
        self.browse_button_id = f"browse_button{id_suffix}"
        
    def setup_ui(self, input_width: int = 400, placeholder_text: str = "No file selected"):
        """Create the file picker UI components."""
        with dpg.group(horizontal=True, parent=self.parent_window):
            # File path input (read-only display)
            dpg.add_input_text(
                tag=self.file_input_id,
                default_value=placeholder_text,
                width=input_width,
                readonly=True,
                hint="Selected CSV file path will appear here"
            )
            
            # Browse button
            dpg.add_button(
                tag=self.browse_button_id,
                label="Browse",
                callback=self._show_file_dialog
            )
        
        # File dialog (hidden by default)
        with dpg.file_dialog(
            tag=self.file_dialog_id,
            directory_selector=False,
            show=False,
            callback=self._file_selected,
            cancel_callback=self._file_dialog_cancelled,
            width=700,
            height=400,
            modal=True
        ):
            dpg.add_file_extension(".csv", color=(255, 255, 0, 255))
            dpg.add_file_extension(".*", color=(255, 255, 255, 255))
    
    def _show_file_dialog(self):
        """Show the file selection dialog."""
        dpg.show_item(self.file_dialog_id)
    
    def _file_selected(self, sender, app_data):
        """Handle file selection from dialog."""
        file_path = app_data['file_path_name']
        self.selected_file = file_path
        
        # Update the display
        display_path = self._get_display_path(file_path)
        dpg.set_value(self.file_input_id, display_path)
        
        # Call the callback if provided
        if self.callback:
            try:
                self.callback(file_path)
            except Exception as e:
                print(f"Error in file picker callback: {e}")
    
    def _file_dialog_cancelled(self):
        """Handle file dialog cancellation."""
        pass  # Do nothing when cancelled
    
    def _get_display_path(self, full_path: str) -> str:
        """Get a display-friendly path (truncate if too long)."""
        if len(full_path) <= 60:
            return full_path
        
        # Show filename and parent directory
        filename = os.path.basename(full_path)
        parent_dir = os.path.basename(os.path.dirname(full_path))
        return f".../{parent_dir}/{filename}"
    
    def get_selected_file(self) -> str:
        """Get the currently selected file path."""
        return self.selected_file
    
    def clear_selection(self):
        """Clear the current file selection."""
        self.selected_file = ""
        dpg.set_value(self.file_input_id, "No file selected")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the file picker."""
        if dpg.does_item_exist(self.browse_button_id):
            dpg.configure_item(self.browse_button_id, enabled=enabled)