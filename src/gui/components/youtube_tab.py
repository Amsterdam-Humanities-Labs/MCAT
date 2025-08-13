import dearpygui.dearpygui as dpg
from typing import Optional, Callable
import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .file_picker import FilePicker
from .column_mapper import ColumnMapper
from utils.csv_handler import CSVHandler
from utils.validation_service import (
    validation_service, ValidationUIController, 
    ButtonStateCommand, FileStatusCommand, ValidationContext
)


class YouTubeTab:
    """YouTube scraper tab component."""
    
    def __init__(self, parent_window: str, state_manager, processing_controller):
        self.parent_window = parent_window
        self.state_manager = state_manager
        self.processing_controller = processing_controller
        
        # UI components
        self.column_mapper: Optional[ColumnMapper] = None
        
        # Validation controller setup
        self.validation_controller = ValidationUIController()
        validation_service.subscribe(self.validation_controller)
        
        # Data
        self.current_df: Optional[pd.DataFrame] = None
        self.csv_info = {}
        
        # UI element IDs
        self.check_button_id = "youtube_check_button"
        self.file_status_id = "youtube_file_status"
        self.tab_container_id = "youtube_tab_container"
        self.column_mapping_group_id = "youtube_column_mapping_group"
        self.file_status_group_id = "youtube_file_status_group"
    
    def setup_ui(self):
        """Create the YouTube tab UI components."""
        # Create a left panel that takes 40% of screen width with right border
        with dpg.child_window(
            tag=self.tab_container_id,
            width=int(1000 * 0.4),  # 40% of screen width
            height=-1,
            border=True,
            horizontal_scrollbar=False
        ):
            # Select csv file section
            dpg.add_text("Select csv file", color=[255, 255, 255])
            dpg.add_spacer(height=10)
            
            # Initialize file picker component
            self.file_picker = FilePicker(
                parent_window=self.tab_container_id,
                callback=self.on_file_selected,
                id_suffix="_youtube"
            )
            self.file_picker.setup_ui(input_width=250, placeholder_text="Select csv file")
            
            dpg.add_spacer(height=20)
            
            # Column Mapping Section (hidden initially)
            with dpg.group(tag=self.column_mapping_group_id, show=False):
                dpg.add_text("Csv column mappings", color=[255, 255, 255])
                dpg.add_spacer(height=10)
                
                self.column_mapper = ColumnMapper(
                    parent_window=self.column_mapping_group_id,
                    platform="youtube",
                    callback=self.on_column_mapped
                )
                self.column_mapper.setup_ui()
                
                dpg.add_spacer(height=20)
            
            # File Status Section (hidden initially)
            with dpg.group(tag=self.file_status_group_id, show=False):
                dpg.add_text("File status", color=[255, 255, 255])
                dpg.add_spacer(height=10)
                
                with dpg.group(tag=self.file_status_id):
                    dpg.add_text("No file loaded", color=[180, 180, 180])
                
                dpg.add_spacer(height=20)
                
                # Check moderation status button
                dpg.add_button(
                    tag=self.check_button_id,
                    label="Check moderation status",
                    callback=self._start_processing,
                    enabled=False,
                    width=-1
                )
    
    
    def on_file_selected(self, file_path: str):
        """Handle file selection from file picker."""
        try:
            # Load CSV using our CSV handler
            self.current_df = CSVHandler.load_csv(file_path)
            self.csv_info = CSVHandler.get_csv_info(self.current_df)
            
            # Show column mapping and file status sections
            if dpg.does_item_exist(self.column_mapping_group_id):
                dpg.configure_item(self.column_mapping_group_id, show=True)
            if dpg.does_item_exist(self.file_status_group_id):
                dpg.configure_item(self.file_status_group_id, show=True)
            
            # Populate column mapper with CSV columns
            if self.column_mapper:
                self.column_mapper.populate_dropdowns(self.csv_info['columns'])
            
            # Setup validation UI commands
            self._setup_validation_commands()
            
            # Run initial validation
            self._trigger_validation()
            
        except Exception as e:
            # Hide sections on error
            if dpg.does_item_exist(self.column_mapping_group_id):
                dpg.configure_item(self.column_mapping_group_id, show=False)
            if dpg.does_item_exist(self.file_status_group_id):
                dpg.configure_item(self.file_status_group_id, show=False)
            
            self._clear_csv_data()
            
            # Clear validation state
            validation_service.clear_validation()
            
            # Clear column mapper on error
            if self.column_mapper:
                self.column_mapper.clear_selections()
    
    def on_column_mapped(self, col_type: str, selected_value: str, mapping: dict):
        """Handle column mapping changes."""
        # Trigger real-time validation through service
        self._trigger_validation()
    
    def _start_processing(self):
        """Start the URL processing."""
        # Check if validation passed using service
        if not validation_service.is_valid():
            return  # Button should be disabled, but double-check
        
        if self.current_df is None or not self.column_mapper or not self.processing_controller:
            return
        
        # Get column mapping
        column_mapping = self.column_mapper.get_column_mapping()
        
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
            pass  # Error handling will be done by processing controller
    
    def _cancel_processing(self):
        """Cancel the current processing."""
        if self.processing_controller:
            self.processing_controller.cancel_processing()
        
        self._set_processing_ui_state(False)
    
    def _set_processing_ui_state(self, processing: bool):
        """Update UI elements based on processing state."""
        # Enable/disable check button based on processing AND validation state
        if dpg.does_item_exist(self.check_button_id):
            if processing:
                # Always disable during processing
                dpg.configure_item(self.check_button_id, enabled=False)
            else:
                # When not processing, enable only if validation passes
                enabled = validation_service.is_valid()
                dpg.configure_item(self.check_button_id, enabled=enabled)
        
        # Enable/disable browse button and column mapper
        if self.file_picker:
            self.file_picker.set_enabled(not processing)
        
        if self.column_mapper:
            self.column_mapper.set_enabled(not processing)
    
    def update_processing_results(self, result):
        """Handle processing completion."""
        self._set_processing_ui_state(False)
        
        # Log successful processing completion
        print(f"\n✅ PROCESSING COMPLETED SUCCESSFULLY!")
        print(f"📊 Results Summary:")
        print(f"   • Total URLs processed: {result.processed_count}")
        print(f"   • Live URLs: {result.stats.get('live', 0)}")
        print(f"   • Removed URLs: {result.stats.get('removed', 0)}")
        print(f"   • Restricted URLs: {result.stats.get('restricted', 0)}")
        print(f"   • Errors: {result.stats.get('errors', 0)}")
        print(f"🎯 Processing completed without errors!\n")
        
        # Results will be shown in the data space (right panel) - to be implemented later
    
    def handle_processing_error(self, error_message: str):
        """Handle processing error."""
        self._set_processing_ui_state(False)
        
        # Log processing error
        print(f"\n❌ PROCESSING FAILED!")
        print(f"🚨 Error: {error_message}")
        print(f"💡 Please check your CSV file and column mappings.\n")
    
    def _export_results(self, file_path: str) -> bool:
        """Export results to file."""
        if self.processing_controller:
            try:
                return self.processing_controller.export_results(file_path)
            except Exception as e:
                print(f"Export error: {e}")
                return False
        return False
    
    def _setup_validation_commands(self):
        """Setup UI commands for validation responses."""
        # Clear any existing commands
        self.validation_controller.commands.clear()
        
        # Add button state command
        button_command = ButtonStateCommand(self.check_button_id, enable_on_valid=True)
        self.validation_controller.add_command(button_command)
        
        # Add file status command
        status_command = FileStatusCommand(self.file_status_id)
        self.validation_controller.add_command(status_command)
    
    def _trigger_validation(self):
        """Trigger validation through the service."""
        context = ValidationContext()
        context.csv_df = self.current_df
        context.csv_filename = ""
        if self.file_picker and self.file_picker.get_selected_file():
            context.csv_filename = os.path.basename(self.file_picker.get_selected_file())
        
        context.column_mapping = self.column_mapper.get_column_mapping() if self.column_mapper else {}
        context.csv_columns = self.csv_info.get('columns', [])
        
        # Trigger validation through service (will notify all observers)
        result = validation_service.validate(context)
        print(f"DEBUG: Validation result: {result.is_valid()}, Errors: {result.errors}")
    
    
    def _clear_csv_data(self):
        """Clear CSV data and reset displays."""
        self.current_df = None
        self.csv_info = {}
        self._update_file_status()
    
    def cleanup(self):
        """Clean up tab resources."""
        # Unsubscribe from validation service
        validation_service.unsubscribe(self.validation_controller)