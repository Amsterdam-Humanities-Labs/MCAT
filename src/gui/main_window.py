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
from gui.components.column_mapper import ColumnMapper
from gui.components.progress_display import ProgressDisplay
from gui.components.results_table import ResultsTable
from gui.components.export_panel import ExportPanel
from gui.processing_controller import ProcessingController


class MainWindow:
    """Primary GUI controller using Dear PyGui."""
    
    def __init__(self):
        self.state_manager = StateManager()
        self.file_picker: Optional[FilePicker] = None
        self.column_mapper: Optional[ColumnMapper] = None
        self.progress_display: Optional[ProgressDisplay] = None
        self.results_table: Optional[ResultsTable] = None
        self.export_panel: Optional[ExportPanel] = None
        self.processing_controller: Optional[ProcessingController] = None
        self.current_df: Optional[pd.DataFrame] = None
        self.csv_info = {}
        
        # UI element IDs
        self.main_window_id = "main_window"
        self.status_text_id = "status_text"
        self.csv_info_text_id = "csv_info_text"
        self.columns_list_id = "columns_list"
        self.start_button_id = "start_processing_button"
        
        # Initialize processing controller
        self.processing_controller = ProcessingController(self.state_manager)
        self.processing_controller.set_callbacks(
            on_processing_complete=self._on_processing_complete,
            on_processing_error=self._on_processing_error
        )
        
        # Subscribe to state changes
        self.state_manager.subscribe(self._on_state_changed)
    
    def setup_ui(self):
        """Create the main window UI."""
        # Create main window
        with dpg.window(
            tag=self.main_window_id,
            label="MCAT Content Moderation Checker",
            width=1000,
            height=800,
            pos=[50, 50]
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
            dpg.add_spacer()
            
            # Initialize file picker component
            self.file_picker = FilePicker(
                parent_window=self.main_window_id,
                callback=self.on_file_selected
            )
            self.file_picker.setup_ui()
            
            dpg.add_spacer()
            dpg.add_separator()
            
            # Platform Selection
            dpg.add_text("Platform:", color=[200, 200, 255])
            dpg.add_text("YouTube (MVP)", color=[150, 150, 200])
            
            dpg.add_spacer()
            dpg.add_separator()
            
            # Column Mapping Section
            self.column_mapper = ColumnMapper(
                parent_window=self.main_window_id,
                platform="youtube",
                callback=self.on_column_mapped
            )
            self.column_mapper.setup_ui()
            
            dpg.add_spacer()
            dpg.add_separator()
            
            # Processing Controls
            dpg.add_text("Processing:", color=[200, 200, 255])
            dpg.add_spacer()
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    tag=self.start_button_id,
                    label="Start Processing",
                    callback=self._start_processing,
                    enabled=False
                )
                dpg.add_button(
                    label="Cancel",
                    callback=self._cancel_processing,
                    enabled=False
                )
            
            dpg.add_spacer()
            
            # Progress Display
            self.progress_display = ProgressDisplay(self.main_window_id)
            self.progress_display.setup_ui()
            
            dpg.add_spacer()
            dpg.add_separator()
            
            # CSV Information Section
            dpg.add_text("CSV Information:", color=[200, 200, 255])
            dpg.add_spacer()
            
            dpg.add_text(
                tag=self.csv_info_text_id,
                default_value="No file loaded",
                color=[180, 180, 180]
            )
            
            dpg.add_spacer()
            
            # Columns List
            dpg.add_text("Available Columns:", color=[150, 150, 200])
            with dpg.child_window(
                tag=self.columns_list_id,
                height=150,
                border=True
            ):
                dpg.add_text("Load a CSV file to see columns", color=[120, 120, 120])
            
            dpg.add_spacer()
            dpg.add_separator()
            
            # Results Section
            dpg.add_text("Results:", color=[200, 200, 255])
            dpg.add_spacer()
            
            self.results_table = ResultsTable(self.main_window_id)
            self.results_table.setup_ui()
            
            dpg.add_spacer()
            dpg.add_separator()
            
            # Export Section
            self.export_panel = ExportPanel(
                self.main_window_id, 
                export_callback=self._export_results
            )
            self.export_panel.setup_ui()
            
            dpg.add_spacer()
            dpg.add_separator()
            
            # Status Section
            dpg.add_text("Status:", color=[200, 200, 255])
            dpg.add_text(
                tag=self.status_text_id,
                default_value="Ready - Select a CSV file to begin",
                color=[100, 255, 100]
            )
    
    def run(self):
        """Start the GUI application."""
        dpg.create_context()
        dpg.create_viewport(title="MCAT Content Moderation Checker", width=1050, height=850)
        
        self.setup_ui()
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.main_window_id, True)
        
        try:
            dpg.start_dearpygui()
        finally:
            # Cleanup processing controller
            if self.processing_controller:
                self.processing_controller.cleanup()
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
            
            # Populate column mapper with CSV columns
            if self.column_mapper:
                self.column_mapper.populate_dropdowns(self.csv_info['columns'])
            
            self._update_status(f"CSV loaded successfully: {file_path}", [100, 255, 100])
            
        except Exception as e:
            error_msg = f"Error loading CSV: {str(e)}"
            self._update_status(error_msg, [255, 100, 100])
            self._clear_csv_data()
            
            # Clear column mapper on error
            if self.column_mapper:
                self.column_mapper.clear_selections()
            
            # Disable start button
            if dpg.does_item_exist(self.start_button_id):
                dpg.configure_item(self.start_button_id, enabled=False)
    
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
    
    def on_column_mapped(self, col_type: str, selected_value: str, mapping: dict):
        """Handle column mapping changes."""
        # Validate mapping and enable/disable start button
        if self.column_mapper:
            is_valid, message = self.column_mapper.validate_mapping()
            
            if dpg.does_item_exist(self.start_button_id):
                dpg.configure_item(self.start_button_id, enabled=is_valid)
            
            if is_valid:
                self._update_status("Ready to process - Click Start Processing", [100, 255, 100])
            else:
                self._update_status(f"Column mapping: {message}", [255, 255, 100])
    
    def _start_processing(self):
        """Start the URL processing."""
        if self.current_df is None or not self.column_mapper or not self.processing_controller:
            self._update_status("No CSV file loaded", [255, 100, 100])
            return
        
        # Get column mapping
        column_mapping = self.column_mapper.get_column_mapping()
        is_valid, message = self.column_mapper.validate_mapping()
        
        if not is_valid:
            self._update_status(f"Invalid mapping: {message}", [255, 100, 100])
            return
        
        try:
            # Start processing
            self.processing_controller.start_processing(
                df=self.current_df,
                column_mapping=column_mapping,
                platform="youtube"
            )
            
            # Update UI state
            self._set_processing_ui_state(True)
            
        except Exception as e:
            self._update_status(f"Failed to start processing: {e}", [255, 100, 100])
    
    def _cancel_processing(self):
        """Cancel the current processing."""
        if self.processing_controller:
            self.processing_controller.cancel_processing()
        
        self._set_processing_ui_state(False)
    
    def _set_processing_ui_state(self, processing: bool):
        """Update UI elements based on processing state."""
        # Enable/disable buttons
        if dpg.does_item_exist(self.start_button_id):
            dpg.configure_item(self.start_button_id, enabled=not processing)
        
        # Enable/disable file picker and column mapper
        if self.file_picker:
            self.file_picker.set_enabled(not processing)
        
        if self.column_mapper:
            self.column_mapper.set_enabled(not processing)
        
        if self.export_panel:
            self.export_panel.set_enabled(not processing)
    
    def _on_processing_complete(self, result):
        """Handle processing completion."""
        if self.results_table:
            self.results_table.update_results(result.dataframe)
        
        if self.export_panel:
            self.export_panel.set_results(result.dataframe)
        
        self._set_processing_ui_state(False)
        self._update_status(f"Processing completed! {result.processed_count} URLs processed", [100, 255, 100])
    
    def _on_processing_error(self, error_message: str):
        """Handle processing error."""
        self._set_processing_ui_state(False)
        self._update_status(f"Processing error: {error_message}", [255, 100, 100])
    
    def _export_results(self, file_path: str) -> bool:
        """Export results to file."""
        if self.processing_controller:
            try:
                return self.processing_controller.export_results(file_path)
            except Exception as e:
                print(f"Export error: {e}")
                return False
        return False
    
    def _on_state_changed(self, state: ProcessingState, data: dict):
        """Handle state manager updates."""
        # Update progress display
        if self.progress_display:
            self.progress_display.update_progress(state, data)
        
        # Update main status
        status_colors = {
            ProcessingState.IDLE: [100, 255, 100],
            ProcessingState.LOADING_CSV: [255, 255, 100],
            ProcessingState.ERROR: [255, 100, 100],
            ProcessingState.COMPLETED: [100, 255, 100]
        }
        
        color = status_colors.get(state, [255, 255, 255])
        if state not in [ProcessingState.PROCESSING_URLS]:  # Don't override processing status
            self._update_status(state.value, color)
