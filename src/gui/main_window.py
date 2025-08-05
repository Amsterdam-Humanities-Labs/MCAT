import dearpygui.dearpygui as dpg
import pandas as pd
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from utils.csv_handler import CSVHandler
from utils.state_manager import StateManager, ProcessingState
from gui.components.file_picker import FilePicker


class MainWindow:
    """Primary GUI controller using Dear PyGui."""
    
    def __init__(self):
        self.state_manager = StateManager()
        self.file_picker: Optional[FilePicker] = None
        self.current_df: Optional[pd.DataFrame] = None
        self.csv_info = {}
        
        # UI element IDs
        self.main_window_id = "main_window"
        self.status_text_id = "status_text"
        self.csv_info_text_id = "csv_info_text"
        self.columns_list_id = "columns_list"
        
        # Subscribe to state changes
        self.state_manager.subscribe(self._on_state_changed)
    
    def setup_ui(self):
        """Create the main window UI."""
        # Create main window
        with dpg.window(
            tag=self.main_window_id,
            label="MCAT Content Moderation Checker - CSV Loading Test",
            width=800,
            height=600,
            pos=[100, 100]
        ):

            # Load larger font for 4K display
            with dpg.font_registry():
                font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       "assets", "fonts", "NotoSans-Medium.ttf")
                large_font = dpg.add_font(font_path, 36)  # 20px for 4K, adjust as needed
            
            dpg.bind_font(large_font)
 
            # Title
            dpg.add_text("MCAT Content Moderation Checker", color=[255, 255, 255])
            dpg.add_separator()
            
            # File Selection Section
            dpg.add_text("File Selection:", color=[200, 200, 255])
            dpg.add_spacing()
            
            # Initialize file picker component
            self.file_picker = FilePicker(
                parent_window=self.main_window_id,
                callback=self.on_file_selected
            )
            self.file_picker.setup_ui()
            
            dpg.add_spacing()
            dpg.add_separator()
            
            # CSV Information Section
            dpg.add_text("CSV Information:", color=[200, 200, 255])
            dpg.add_spacing()
            
            dpg.add_text(
                tag=self.csv_info_text_id,
                default_value="No file loaded",
                color=[180, 180, 180]
            )
            
            dpg.add_spacing()
            
            # Columns List
            dpg.add_text("Available Columns:", color=[150, 150, 200])
            with dpg.child_window(
                tag=self.columns_list_id,
                height=150,
                border=True
            ):
                dpg.add_text("Load a CSV file to see columns", color=[120, 120, 120])
            
            dpg.add_spacing()
            dpg.add_separator()
            
            # Status Section
            dpg.add_text("Status:", color=[200, 200, 255])
            dpg.add_text(
                tag=self.status_text_id,
                default_value="Ready - Select a CSV file to begin",
                color=[100, 255, 100]
            )
            
            dpg.add_spacing()
            
            # Test buttons (for development)
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Clear File",
                    callback=self._clear_file
                )
                dpg.add_button(
                    label="Reload File",
                    callback=self._reload_file
                )
    
    def run(self):
        """Start the GUI application."""
        dpg.create_context()
        dpg.create_viewport(title="MCAT - CSV Loading Test", width=850, height=650)
        
        self.setup_ui()
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.main_window_id, True)
        
        try:
            dpg.start_dearpygui()
        finally:
            dpg.destroy_context()
    
    def on_file_selected(self, file_path: str):
        """Handle file selection from file picker."""
        try:
            self._update_status("Loading CSV file...", [255, 255, 100])
            
            # Load CSV using our CSV handler
            self.current_df = CSVHandler.load_csv(file_path)
            self.csv_info = CSVHandler.get_csv_info(self.current_df)
            
            # Update UI with CSV information
            self._update_csv_info()
            self._update_columns_list()
            self._update_status(f"CSV loaded successfully: {file_path}", [100, 255, 100])
            
        except Exception as e:
            error_msg = f"Error loading CSV: {str(e)}"
            self._update_status(error_msg, [255, 100, 100])
            self._clear_csv_data()
    
    def _update_csv_info(self):
        """Update the CSV information display."""
        if self.csv_info:
            info_text = (
                f"Rows: {self.csv_info['rows']}\n"
                f"Columns: {self.csv_info['column_count']}\n"
                f"File loaded successfully"
            )
            dpg.set_value(self.csv_info_text_id, info_text)
            dpg.configure_item(self.csv_info_text_id, color=[100, 255, 100])
        else:
            dpg.set_value(self.csv_info_text_id, "No file loaded")
            dpg.configure_item(self.csv_info_text_id, color=[180, 180, 180])
    
    def _update_columns_list(self):
        """Update the columns list display."""
        # Clear existing items
        dpg.delete_item(self.columns_list_id, children_only=True)
        
        if self.csv_info and 'columns' in self.csv_info:
            with dpg.group(parent=self.columns_list_id):
                for i, column in enumerate(self.csv_info['columns']):
                    color = [200, 200, 255] if i % 2 == 0 else [180, 180, 235]
                    dpg.add_text(f"• {column}", color=color)
        else:
            dpg.add_text("Load a CSV file to see columns", 
                        color=[120, 120, 120], 
                        parent=self.columns_list_id)
    
    def _update_status(self, message: str, color: list = None):
        """Update the status display."""
        dpg.set_value(self.status_text_id, message)
        if color:
            dpg.configure_item(self.status_text_id, color=color)
    
    def _clear_file(self):
        """Clear the current file selection."""
        if self.file_picker:
            self.file_picker.clear_selection()
        self._clear_csv_data()
        self._update_status("File cleared - Select a CSV file to begin", [100, 255, 100])
    
    def _reload_file(self):
        """Reload the current file."""
        if self.file_picker and self.file_picker.get_selected_file():
            file_path = self.file_picker.get_selected_file()
            self.on_file_selected(file_path)
        else:
            self._update_status("No file selected to reload", [255, 255, 100])
    
    def _clear_csv_data(self):
        """Clear CSV data and reset displays."""
        self.current_df = None
        self.csv_info = {}
        self._update_csv_info()
        self._update_columns_list()
    
    def _on_state_changed(self, state: ProcessingState, data: dict):
        """Handle state manager updates."""
        status_colors = {
            ProcessingState.IDLE: [100, 255, 100],
            ProcessingState.LOADING_CSV: [255, 255, 100],
            ProcessingState.ERROR: [255, 100, 100],
            ProcessingState.COMPLETED: [100, 255, 100]
        }
        
        color = status_colors.get(state, [255, 255, 255])
        self._update_status(state.value, color)
