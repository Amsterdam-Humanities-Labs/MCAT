import dearpygui.dearpygui as dpg
from typing import Optional
import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from ..widgets.file_input_picker import FilePicker
from ..panels.panel_column_selector import PanelPreserveColumns
from ..widgets.progress_bar_segmented import RectangularProgress
from ..widgets.button_group_processing import ProcessingControls
from ...controllers.processing_workflow_controller import ProcessingCoordinator
from src.utils.csv_handler import CSVHandler
from src.utils.validation_service import (
    validation_service, ValidationUIController, 
    ButtonStateCommand, FileStatusCommand, ValidationContext
)


class YouTubeTab:
    """Simplified YouTube scraper tab with proper separation of concerns."""
    
    def __init__(self, parent_window: str, processing_controller, state_manager=None):
        self.parent_window = parent_window
        
        # Core components with single responsibilities
        self.file_picker: Optional[FilePicker] = None
        self.column_selector: Optional[PanelPreserveColumns] = None
        self.progress_display: Optional[RectangularProgress] = None
        self.processing_controls: Optional[ProcessingControls] = None
        self.processing_coordinator = ProcessingCoordinator(processing_controller)
        
        # Validation
        self.validation_controller = ValidationUIController()
        validation_service.subscribe(self.validation_controller)
        
        # Current data
        self.current_df: Optional[pd.DataFrame] = None
        self.csv_info = {}
        self.results_df: Optional[pd.DataFrame] = None
        self.video_url_column = ""
        self.preserved_columns = []
        
        # Export file picker
        self.export_file_picker: Optional[FilePicker] = None
        
        # UI element IDs
        self.left_panel_id = "youtube_left_panel"
        self.right_panel_id = "youtube_right_panel"
        self.preserve_columns_group_id = "youtube_preserve_columns_group"
        self.file_status_group_id = "youtube_file_status_group"
        self.file_status_id = "youtube_file_status"
        self.results_section_id = "youtube_results_section"
        self.results_table_id = "youtube_results_table"
        
        # Callbacks will be setup after UI components are created
    
    def setup_ui(self):
        """Create the YouTube tab UI with clean component separation."""
        with dpg.group(horizontal=True, parent=self.parent_window):
            self._setup_left_panel()
            self._setup_right_panel()
        
        # Setup callbacks after UI components are created
        self._setup_callbacks()
    
    def _setup_left_panel(self):
        """Setup the left control panel (40% width)."""
        with dpg.child_window(
            tag=self.left_panel_id,
            width=int(1000 * 0.4),
            height=-1,
            border=True,
            horizontal_scrollbar=False
        ):
            # File selection
            self._setup_file_section()
            dpg.add_spacer(height=20)
            
            # Column selection (hidden initially)
            self._setup_column_section()
            dpg.add_spacer(height=20)
            
            # File status and validation (hidden initially)
            self._setup_status_section()
            dpg.add_spacer(height=20)
            
            # Processing controls
            self._setup_processing_section()
    
    def _setup_right_panel(self):
        """Setup the right data panel (60% width)."""
        with dpg.child_window(
            tag=self.right_panel_id,
            width=-1,
            height=-1,
            border=False,
            horizontal_scrollbar=False
        ):
            dpg.add_text("YouTube Data", color=[255, 255, 255])
            dpg.add_spacer(height=20)
            
            # Progress display
            self.progress_display = RectangularProgress(
                parent_window=self.right_panel_id,
                width=400,
                height=50
            )
            self.progress_display.setup_ui(label="Processing Progress")
            
            dpg.add_spacer(height=20)
            
            # Results section
            self._setup_results_section()
    
    def _setup_file_section(self):
        """Setup file selection section."""
        dpg.add_text("Select CSV file", color=[255, 255, 255])
        dpg.add_spacer(height=10)
        
        self.file_picker = FilePicker(
            parent_window=self.left_panel_id,
            callback=self._on_file_selected,
            id_suffix="_youtube"
        )
        self.file_picker.setup_ui(input_width=250, placeholder_text="Select csv file")
    
    def _setup_column_section(self):
        """Setup column selection section."""
        with dpg.group(tag=self.preserve_columns_group_id, show=False):
            self.column_selector = PanelPreserveColumns(
                parent_window=self.preserve_columns_group_id,
                callback=self._on_columns_changed
            )
            self.column_selector.setup_ui()
    
    def _setup_status_section(self):
        """Setup file status and validation section."""
        with dpg.group(tag=self.file_status_group_id, show=False):
            dpg.add_text("File status", color=[255, 255, 255])
            dpg.add_spacer(height=10)
            
            with dpg.group(tag=self.file_status_id):
                dpg.add_text("No file loaded", color=[180, 180, 180])
    
    def _setup_processing_section(self):
        """Setup processing controls section."""
        self.processing_controls = ProcessingControls(self.left_panel_id)
        self.processing_controls.setup_ui("Check moderation status")
    
    def _setup_results_section(self):
        """Setup results table and export section."""
        with dpg.group(tag=self.results_section_id, show=False):
            dpg.add_text("Results", color=[255, 255, 255])
            dpg.add_spacer(height=10)
            
            # Results table with horizontal scrolling
            with dpg.table(
                tag=self.results_table_id,
                header_row=True,
                resizable=True,
                policy=dpg.mvTable_SizingFixedFit,
                borders_innerH=True,
                borders_outerH=True,
                borders_innerV=True,
                borders_outerV=True,
                row_background=True,
                scrollX=True,  # Enable horizontal scrolling
                height=300  # Fixed height for scrolling
            ):
                pass  # Columns will be added dynamically
            
            dpg.add_spacer(height=10)
            
            # Export section
            dpg.add_text("Export Results", color=[255, 255, 255])
            dpg.add_spacer(height=5)
            
            # Export file picker
            self.export_file_picker = FilePicker(
                parent_window=self.results_section_id,
                callback=self._on_export_file_selected,
                id_suffix="_export"
            )
            self.export_file_picker.setup_ui(
                input_width=300, 
                placeholder_text="Choose export location..."
            )
    
    def _setup_callbacks(self):
        """Setup all component callbacks."""
        # Processing coordinator callbacks
        self.processing_coordinator.set_callbacks(
            on_progress_update=self._on_progress_update,
            on_processing_complete=self._on_processing_complete,
            on_processing_error=self._on_processing_error,
            on_ui_state_change=self._on_processing_state_changed
        )
        
        # Processing controls callbacks
        if self.processing_controls:
            self.processing_controls.set_callbacks(
                on_start=self._start_processing,
                on_pause=self._pause_processing,
                on_resume=self._resume_processing,
                on_cancel=self._cancel_processing
            )
    
    def _on_file_selected(self, file_path: str):
        """Handle file selection."""
        try:
            self.current_df = CSVHandler.load_csv(file_path)
            self.csv_info = CSVHandler.get_csv_info(self.current_df)
            
            # Show dependent sections
            if dpg.does_item_exist(self.preserve_columns_group_id):
                dpg.configure_item(self.preserve_columns_group_id, show=True)
            if dpg.does_item_exist(self.file_status_group_id):
                dpg.configure_item(self.file_status_group_id, show=True)
            
            # Populate columns
            if self.column_selector:
                self.column_selector.populate_columns(self.csv_info['columns'])
            
            # Setup validation
            self._setup_validation()
            self._trigger_validation()
            
        except Exception as e:
            self._handle_file_error()
    
    def _on_columns_changed(self, change_type: str, data: dict):
        """Handle column selection changes."""
        self._trigger_validation()
    
    def _start_processing(self):
        """Start processing workflow."""
        if not validation_service.is_valid() or not self.column_selector:
            return
        
        columns_data = self.column_selector.get_all_selected_columns()
        column_mapping = {'post': columns_data['post_column']}
        
        self.processing_coordinator.start_processing(
            self.current_df, 
            column_mapping, 
            "youtube"
        )
    
    def _pause_processing(self):
        """Pause processing."""
        self.processing_coordinator.pause_processing()
    
    def _resume_processing(self):
        """Resume processing."""
        self.processing_coordinator.resume_processing()
    
    def _cancel_processing(self):
        """Cancel processing and reset."""
        self.processing_coordinator.cancel_processing()
        if self.progress_display:
            self.progress_display.reset()
    
    def _on_progress_update(self, current_stats: dict, total_count: int, processed_count: int, current_action: str = ""):
        """Handle progress updates."""
        if self.progress_display:
            pending_count = max(0, total_count - processed_count)
            progress_counts = {
                'pending': pending_count,
                'live': current_stats.get('live', 0),
                'removed': current_stats.get('removed', 0),
                'restricted': current_stats.get('restricted', 0),
                'error': current_stats.get('errors', 0),
                'skipped': current_stats.get('skipped', 0)
            }
            self.progress_display.update_progress(progress_counts, total_count, processed_count)
            
            # Update latest URL if provided
            if current_action:
                # Extract URL from "Checking: <url>" format
                if current_action.startswith("Checking: "):
                    url = current_action[10:]  # Remove "Checking: " prefix
                    self.progress_display.update_latest_url(url)
    
    def _on_processing_complete(self, result):
        """Handle processing completion."""
        # Ensure progress bar shows completion with no pending items
        if self.progress_display:
            # Get final stats and ensure no pending items
            final_counts = {
                'pending': 0,  # No pending items when complete
                'live': result.stats.get('live', 0),
                'removed': result.stats.get('removed', 0), 
                'restricted': result.stats.get('restricted', 0),
                'error': result.stats.get('errors', 0),
                'skipped': result.stats.get('skipped', 0)
            }
            self.progress_display.update_progress(final_counts, result.processed_count, result.processed_count)
            # Clear the latest URL display when processing completes
            self.progress_display.clear_latest_url()
            
        print(f"✅ Processing completed: {result.processed_count} URLs processed")
        
        # Show results table if we have results
        if hasattr(result, 'dataframe') and result.dataframe is not None:
            self._populate_results_table(result.dataframe)
    
    def _on_processing_error(self, error_message: str):
        """Handle processing error."""
        print(f"❌ Processing error: {error_message}")
    
    def _on_processing_state_changed(self, is_processing: bool, is_paused: bool):
        """Handle processing state changes."""
        if self.processing_controls:
            self.processing_controls.set_processing_state(is_processing, is_paused)
        
        # Enable/disable other components
        if self.file_picker:
            self.file_picker.set_enabled(not is_processing)
        if self.column_selector:
            self.column_selector.set_enabled(not is_processing)
    
    def _setup_validation(self):
        """Setup validation UI commands."""
        self.validation_controller.commands.clear()
        
        if self.processing_controls:
            button_command = ButtonStateCommand(
                self.processing_controls.start_button_id, 
                enable_on_valid=True
            )
            self.validation_controller.add_command(button_command)
        
        status_command = FileStatusCommand(self.file_status_id)
        self.validation_controller.add_command(status_command)
    
    def _trigger_validation(self):
        """Trigger validation check."""
        context = ValidationContext()
        context.csv_df = self.current_df
        context.csv_filename = ""
        
        if self.file_picker and self.file_picker.get_selected_file():
            context.csv_filename = os.path.basename(self.file_picker.get_selected_file())
        
        if self.column_selector:
            columns_data = self.column_selector.get_all_selected_columns()
            context.post_column = columns_data['post_column']
            context.preserve_columns = columns_data['preserve_columns']
        
        context.csv_columns = self.csv_info.get('columns', [])
        validation_service.validate(context)
    
    def _handle_file_error(self):
        """Handle file loading errors."""
        if dpg.does_item_exist(self.preserve_columns_group_id):
            dpg.configure_item(self.preserve_columns_group_id, show=False)
        if dpg.does_item_exist(self.file_status_group_id):
            dpg.configure_item(self.file_status_group_id, show=False)
        
        self.current_df = None
        self.csv_info = {}
        validation_service.clear_validation()
        
        if self.column_selector:
            self.column_selector.clear_selections()
    
    def _populate_results_table(self, results_df: pd.DataFrame):
        """Populate the results table with processed data."""
        self.results_df = results_df
        
        # Debug: Print DataFrame info
        print(f"📊 Results DataFrame shape: {results_df.shape}")
        print(f"📊 Results DataFrame columns: {list(results_df.columns)}")
        print(f"📊 First few rows:\n{results_df.head()}")
        
        # Get column mapping info
        if self.column_selector:
            columns_data = self.column_selector.get_all_selected_columns()
            self.video_url_column = columns_data['post_column']
            self.preserved_columns = columns_data['preserve_columns']
            print(f"📊 Video URL column: {self.video_url_column}")
            print(f"📊 Preserved columns: {self.preserved_columns}")
        
        # Clear existing table content
        if dpg.does_item_exist(self.results_table_id):
            # Delete existing columns and rows
            children = dpg.get_item_children(self.results_table_id)
            if children:
                for child_list in children.values():
                    for child in child_list:
                        dpg.delete_item(child)
        
        # Define column order: Video URL, Status, then preserved columns
        table_columns = [self.video_url_column, 'status'] + self.preserved_columns
        
        # Debug: Check which columns actually exist
        available_columns = [col for col in table_columns if col in results_df.columns]
        missing_columns = [col for col in table_columns if col not in results_df.columns]
        print(f"📊 Available columns: {available_columns}")
        print(f"📊 Missing columns: {missing_columns}")
        
        # Use only available columns
        table_columns = available_columns
        
        # Add table columns
        for i, col_name in enumerate(table_columns):
            if col_name == self.video_url_column:
                display_name = "Video URL"
            elif col_name == 'status':
                display_name = "Moderation Status"
            else:
                display_name = col_name.replace('_', ' ').title()
            
            dpg.add_table_column(
                label=display_name,
                parent=self.results_table_id,
                width_fixed=True,
                init_width_or_weight=200 if col_name == self.video_url_column else 150
            )
        
        # Status colors mapping (same as progress bar)
        status_colors = {
            'Live': (0, 180, 0),          # Green
            'Removed': (220, 50, 50),     # Red  
            'Age-restricted': (255, 140, 0),  # Orange
            'Geo-blocked': (255, 140, 0),     # Orange
            'Private': (255, 140, 0),         # Orange
            'Restricted': (255, 140, 0),      # Orange
            'Error': (150, 30, 30),           # Dark red
        }
        
        # Add table rows
        for _, row in results_df.iterrows():
            with dpg.table_row(parent=self.results_table_id):
                for col_name in table_columns:
                    value = row.get(col_name, "")
                    
                    # Simple text display - users will use CSV export for data access
                    cell_value = str(value) if value is not None else ""
                    
                    if col_name == 'status':
                        # Color-coded status text
                        color = status_colors.get(cell_value, (200, 200, 200))  # Default gray
                        dpg.add_text(cell_value, color=color)
                    else:
                        # Regular text for other columns
                        dpg.add_text(cell_value)
        
        # Show the results section
        if dpg.does_item_exist(self.results_section_id):
            dpg.configure_item(self.results_section_id, show=True)
    
    def _on_export_file_selected(self, file_path: str):
        """Handle export file selection using our FilePicker component."""
        if self.results_df is None:
            print("❌ No results to export")
            return
        
        try:
            # Ensure .csv extension
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            
            # Create export DataFrame with only displayed columns (same as table)
            export_columns = [self.video_url_column, 'status'] + self.preserved_columns
            
            # Filter to only include columns that exist in the results
            available_export_columns = [col for col in export_columns if col in self.results_df.columns]
            
            # Export only the selected columns
            export_df = self.results_df[available_export_columns]
            export_df.to_csv(file_path, index=False)
            print(f"✅ Results exported to: {file_path}")
            
        except Exception as e:
            print(f"❌ Export error: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        validation_service.unsubscribe(self.validation_controller)