import dearpygui.dearpygui as dpg
from typing import Optional
import pandas as pd

from gui.components.widgets.file_input_picker import FilePicker
from gui.components.panels.panel_column_selector import PanelPreserveColumns
from gui.components.widgets.progress_bar_segmented import RectangularProgress
from gui.components.widgets.button_group_processing import ProcessingControls

# New service imports
from services.csv_service import CSVService
from services.processing_service import ProcessingService
from models.file_models import FileInfo, ColumnMapping
from models.processing_models import ProcessingJob, ProcessingStatus, ProcessingState

from config.settings import UI_SPACING


class YouTubeTab:
    """Simplified YouTube scraper tab with proper separation of concerns."""
    
    def __init__(self, parent_window: str, processing_controller=None, state_manager=None):
        self.parent_window = parent_window
        
        # Business logic services
        self.csv_service = CSVService()
        self.processing_service = ProcessingService()
        
        # UI components 
        self.file_picker: Optional[FilePicker] = None
        self.column_selector: Optional[PanelPreserveColumns] = None
        self.progress_display: Optional[RectangularProgress] = None
        self.processing_controls: Optional[ProcessingControls] = None
        
        # Current data (using new models)
        self.current_file: Optional[FileInfo] = None
        self.current_column_mapping = ColumnMapping()
        self.results_df: Optional[pd.DataFrame] = None
        
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
            dpg.add_spacer(height=UI_SPACING)
            
            # Column selection (hidden initially)
            self._setup_column_section()
            dpg.add_spacer(height=UI_SPACING)
            
            # File status and validation (hidden initially)
            self._setup_status_section()
            dpg.add_spacer(height=UI_SPACING)
            
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
            dpg.add_spacer(height=UI_SPACING)
            
            # Progress display
            self.progress_display = RectangularProgress(
                parent_window=self.right_panel_id,
                width=400,
                height=50
            )
            self.progress_display.setup_ui(label="Processing Progress")
            
            dpg.add_spacer(height=UI_SPACING)
            
            # Results section
            self._setup_results_section()
    
    def _setup_file_section(self):
        """Setup file selection section."""
        self.file_picker = FilePicker(
            parent_window=self.left_panel_id,
            callback=self._on_file_selected,
            id_suffix="_youtube"
        )
        self.file_picker.setup_ui(
            input_width=250, 
            placeholder_text="Select csv file",
            label="Select CSV file"
        )
    
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
            dpg.add_spacer(height=UI_SPACING)
            
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
            dpg.add_spacer(height=UI_SPACING)
            
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
            
            dpg.add_spacer(height=UI_SPACING)
            
            # Export file picker
            self.export_file_picker = FilePicker(
                parent_window=self.results_section_id,
                callback=self._on_export_file_selected,
                id_suffix="_export"
            )
            self.export_file_picker.setup_ui(
                input_width=300, 
                placeholder_text="Choose export location...",
                label="Export Results"
            )
    
    def _setup_callbacks(self):
        """Setup all component callbacks."""
        # Note: Processing service callbacks are now setup in _start_processing method
        
        # Processing controls callbacks
        if self.processing_controls:
            self.processing_controls.set_callbacks(
                on_start=self._start_processing,
                on_pause=self._pause_processing,
                on_resume=self._resume_processing,
                on_cancel=self._cancel_processing
            )
    
    def _on_file_selected(self, file_path: str):
        """Handle file selection - now uses CSV service."""
        # Use CSV service to load and validate file
        file_info = self.csv_service.load_file(file_path)
        self.current_file = file_info
        
        if file_info.valid:
            # Show dependent sections
            if dpg.does_item_exist(self.preserve_columns_group_id):
                dpg.configure_item(self.preserve_columns_group_id, show=True)
            if dpg.does_item_exist(self.file_status_group_id):
                dpg.configure_item(self.file_status_group_id, show=True)
            
            # Populate columns using service
            column_options = self.csv_service.get_column_options(file_info)
            if self.column_selector:
                self.column_selector.populate_columns(column_options)
            
            # Update file status display
            self._update_file_status(f"✅ Loaded: {file_info.filename} ({file_info.row_count} rows, {len(file_info.columns)} columns)")
            
            # Setup validation
            self._setup_validation()
            self._trigger_validation()
        else:
            # Handle file error using service info
            self._update_file_status(f"❌ Error: {file_info.error_message}")
            self._handle_file_error()
    
    def _on_columns_changed(self, change_type: str, data: dict):
        """Handle column selection changes."""
        self._trigger_validation()
    
    def _start_processing(self):
        """Start processing workflow - now uses Processing service."""
        if not self.current_file or not self.current_file.valid or not self.column_selector:
            return
        
        # Get column mapping from UI
        columns_data = self.column_selector.get_all_selected_columns()
        self.current_column_mapping = ColumnMapping(
            post_column=columns_data['post_column'],
            preserve_columns=columns_data['preserve_columns']
        )
        
        # Create processing job
        job = ProcessingJob(
            file_info=self.current_file,
            column_mapping=self.current_column_mapping,
            platform="youtube"
        )
        
        # Setup service callbacks
        self.processing_service.set_callbacks(
            on_progress_update=self._on_progress_update,
            on_completion=self._on_processing_complete,
            on_error=self._on_processing_error
        )
        
        # Clear existing results
        self._clear_results()
        
        # Start processing using service
        if not self.processing_service.start_processing(job):
            self._update_file_status("❌ Failed to start processing")
    
    def _pause_processing(self):
        """Pause processing - now uses Processing service."""
        self.processing_service.pause_processing()
    
    def _resume_processing(self):
        """Resume processing - now uses Processing service."""
        self.processing_service.resume_processing()
    
    def _cancel_processing(self):
        """Cancel processing and reset - now uses Processing service."""
        self.processing_service.cancel_processing()
        if self.progress_display:
            self.progress_display.reset()
    
    def _on_progress_update(self, status: ProcessingStatus):
        """Handle progress updates - now receives ProcessingStatus object."""
        if self.progress_display:
            pending_count = max(0, status.total_count - status.processed_count)
            progress_counts = {
                'pending': pending_count,
                'live': status.stats.get('live', 0),
                'removed': status.stats.get('removed', 0),
                'restricted': status.stats.get('restricted', 0),
                'error': status.stats.get('errors', 0),
                'skipped': status.stats.get('skipped', 0)
            }
            self.progress_display.update_progress(progress_counts, status.total_count, status.processed_count)
            
            # Update latest URL if provided
            if status.current_action:
                # Extract URL from "Checking: <url>" format
                if status.current_action.startswith("Checking: "):
                    url = status.current_action[10:]  # Remove "Checking: " prefix
                    self.progress_display.update_latest_url(url)
    
    def _on_processing_complete(self, result):
        """Handle processing completion - now receives ProcessingResult object."""
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
        
        # Show results table if we have results
        if result.success and result.dataframe is not None:
            self._populate_results_table(result.dataframe)
            self._update_file_status(f"✅ Processing complete: {result.processed_count} URLs processed")
        else:
            self._update_file_status(f"❌ Processing failed: {result.error_message}")
    
    def _on_processing_error(self, error_message: str):
        """Handle processing error."""
        self._update_file_status(f"❌ Processing error: {error_message}")
        if self.progress_display:
            self.progress_display.clear_latest_url()
    
    def _update_file_status(self, message: str):
        """Update file status display."""
        if dpg.does_item_exist(self.file_status_id):
            dpg.set_value(self.file_status_id, message)
    
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
        """Setup validation - simplified for service-based approach."""
        self._trigger_validation()
    
    def _trigger_validation(self):
        """Trigger validation check using services."""
        # Simple validation using services
        is_valid = False
        
        if self.current_file and self.column_selector:
            columns_data = self.column_selector.get_all_selected_columns()
            column_mapping = ColumnMapping(
                post_column=columns_data['post_column'],
                preserve_columns=columns_data['preserve_columns']
            )
            
            # Use CSV service to validate
            validation_result = self.csv_service.validate_column_mapping(self.current_file, column_mapping)
            is_valid = validation_result.valid
            
            if not is_valid and validation_result.errors:
                self._update_file_status(f"❌ {validation_result.error_summary}")
        
        # Update processing button state
        if self.processing_controls:
            self.processing_controls.set_start_enabled(is_valid)
    
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
        
        # Get column mapping info
        if self.column_selector:
            columns_data = self.column_selector.get_all_selected_columns()
            self.video_url_column = columns_data['post_column']
            self.preserved_columns = columns_data['preserve_columns']
        
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
        
        # Use only available columns
        available_columns = [col for col in table_columns if col in results_df.columns]
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
            
        except Exception as e:
            pass
    
    def _clear_results(self):
        """Clear results table and data before starting new processing."""
        # Clear results data
        self.results_df = None
        
        # Hide the results section
        if dpg.does_item_exist(self.results_section_id):
            dpg.configure_item(self.results_section_id, show=False)
        
        # Clear existing table content
        if dpg.does_item_exist(self.results_table_id):
            # Delete existing columns and rows
            children = dpg.get_item_children(self.results_table_id)
            if children:
                for child_list in children.values():
                    for child in child_list:
                        dpg.delete_item(child)
        
        # Reset progress display
        if self.progress_display:
            self.progress_display.reset()
    
    def cleanup(self):
        """Clean up resources."""
        # Cleanup services
        if self.processing_service:
            self.processing_service.cleanup()
