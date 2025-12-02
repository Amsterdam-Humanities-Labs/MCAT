"""
Base tab class implementing common UI logic for all platform tabs.

This class provides shared UI structure and components following the MVP pattern,
with platform-specific behavior delegated to presenters.
"""

import dearpygui.dearpygui as dpg
from typing import Optional
import pandas as pd
from abc import ABC, abstractmethod

from gui.components.widgets.file_input_picker import FilePicker
from gui.components.panels.panel_column_selector import PanelPreserveColumns
from gui.components.widgets.progress_bar_segmented import RectangularProgress
from gui.components.widgets.button_group_processing import ProcessingControls
from models.file_models import FileInfo
from models.processing_models import ProcessingStatus
from config.settings import UI_SPACING


class BaseTab(ABC):
    """Base class for all platform tabs - shared UI logic following MVP pattern."""
    
    def __init__(self, parent_window: str, platform: str):
        """
        Initialize base tab.
        
        Args:
            parent_window: Parent DearPyGUI window ID
            platform: Platform name (e.g., 'youtube', 'facebook')
        """
        self.parent_window = parent_window
        self.platform = platform
        
        # Common UI components (identical across all tabs)
        self.file_picker: Optional[FilePicker] = None
        self.column_selector: Optional[PanelPreserveColumns] = None
        self.progress_display: Optional[RectangularProgress] = None
        self.processing_controls: Optional[ProcessingControls] = None
        self.export_file_picker: Optional[FilePicker] = None
        
        # Results data
        self.results_df: Optional[pd.DataFrame] = None
        
        # Platform-specific UI element IDs
        self.left_panel_id = f"{platform}_left_panel"
        self.right_panel_id = f"{platform}_right_panel"
        self.preserve_columns_group_id = f"{platform}_preserve_columns_group"
        self.file_status_group_id = f"{platform}_file_status_group"
        self.file_status_id = f"{platform}_file_status"
        self.results_section_id = f"{platform}_results_section"
        self.results_table_id = f"{platform}_results_table"
        self.export_section_id = f"{platform}_export_section"
        
        # Platform-specific presenter (created by subclass)
        self.presenter = self._create_presenter()
    
    @abstractmethod
    def _create_presenter(self):
        """Create platform-specific presenter. Must be implemented by subclasses."""
        pass
    
    def setup_ui(self):
        """Setup common UI structure - identical across all platforms."""
        # Main horizontal layout
        with dpg.group(parent=self.parent_window, horizontal=True):
            self._setup_left_panel()   # File selection + controls (40% width)
            self._setup_right_panel()  # Progress + results (60% width)
        
        # Initialize presenter after UI is created
        if self.presenter:
            self.presenter.initialize()
    
    def _setup_left_panel(self):
        """Setup the left control panel - common across all platforms."""
        with dpg.child_window(
            tag=self.left_panel_id,
            width=400,  # Fixed width for consistency
            height=-1,
            border=False,
            horizontal_scrollbar=False
        ):
            # Platform title
            dpg.add_text(f"{self.get_platform_display_name()} Content Analysis", 
                        color=[255, 255, 255])
            dpg.add_spacer(height=UI_SPACING)
            
            # File selection section
            self._setup_file_section()
            dpg.add_spacer(height=UI_SPACING)
            
            # Column selection section
            self._setup_column_section()
            dpg.add_spacer(height=UI_SPACING)
            
            # File status and validation
            self._setup_status_section()
            dpg.add_spacer(height=UI_SPACING)
            
            # Processing controls
            self._setup_processing_section()
    
    def _setup_right_panel(self):
        """Setup the right data panel - common across all platforms."""
        with dpg.child_window(
            tag=self.right_panel_id,
            width=-1,
            height=-1,
            border=False,
            horizontal_scrollbar=False
        ):
            dpg.add_text(f"{self.get_platform_display_name()} Data", color=[255, 255, 255])
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
            id_suffix=f"_{self.platform}"
        )
        self.file_picker.setup_ui(
            input_width=250, 
            placeholder_text="Select CSV file",
            label="Select CSV file"
        )
    
    def _setup_column_section(self):
        """Setup column selection section."""
        with dpg.group(tag=self.preserve_columns_group_id, show=False):
            dpg.add_text("Column Mapping", color=[255, 255, 255])
            dpg.add_spacer(height=5)
            
            self.column_selector = PanelPreserveColumns(
                parent_window=self.preserve_columns_group_id,
                callback=self._on_columns_changed
            )
            self.column_selector.setup_ui()
    
    def _setup_status_section(self):
        """Setup file status and validation section.""" 
        with dpg.group(tag=self.file_status_group_id, show=False):
            dpg.add_text("File Status", color=[255, 255, 255])
            dpg.add_spacer(height=5)
            dpg.add_text("", tag=self.file_status_id, color=[180, 180, 180])
    
    def _setup_processing_section(self):
        """Setup processing control section."""
        dpg.add_text("Processing", color=[255, 255, 255])
        dpg.add_spacer(height=5)
        
        self.processing_controls = ProcessingControls(
            parent_window=self.left_panel_id
        )
        self.processing_controls.setup_ui(start_label=f"Start {self.get_platform_display_name()} Analysis")
        self.processing_controls.set_callbacks(
            on_start=self._on_start_processing,
            on_pause=self._on_pause_processing,
            on_resume=self._on_resume_processing,
            on_cancel=self._on_cancel_processing
        )
    
    def _setup_results_section(self):
        """Setup results display section."""
        with dpg.group(tag=self.results_section_id):
            dpg.add_text("Results", color=[255, 255, 255])
            dpg.add_spacer(height=5)
            
            # Results table (initially empty)
            with dpg.table(
                tag=self.results_table_id,
                header_row=True,
                borders_innerV=True,
                borders_outerV=True,
                borders_innerH=True,
                borders_outerH=True,
                scrollY=True,
                height=300
            ):
                dpg.add_table_column(label="URL")
                dpg.add_table_column(label="Status")
                dpg.add_table_column(label="Info")
                
                # Add placeholder row
                with dpg.table_row():
                    dpg.add_text("No results yet...")
                    dpg.add_text("")
                    dpg.add_text("")
            
            dpg.add_spacer(height=UI_SPACING)
            
            # Export section
            self._setup_export_section()
    
    def _setup_export_section(self):
        """Setup export results section."""
        with dpg.group(tag=self.export_section_id):
            dpg.add_text("Export Results", color=[255, 255, 255])
            dpg.add_spacer(height=5)
            
            self.export_file_picker = FilePicker(
                parent_window=self.export_section_id,
                callback=self._on_export_file_selected,
                id_suffix=f"_{self.platform}_export"
            )
            self.export_file_picker.setup_ui(
                input_width=250,
                placeholder_text="Choose export location...",
                label="Export Results"
            )
    
    # UI event handlers (delegate to presenter)
    
    def _on_file_selected(self, file_path: str):
        """Handle file selection - delegate to presenter."""
        if self.presenter:
            self.presenter.handle_file_selected(file_path)
    
    def _on_columns_changed(self, change_type: str, data: dict):
        """Handle column selection changes - delegate to presenter."""
        if self.presenter:
            self.presenter.handle_column_mapping_changed(
                data.get('post_column', ''),
                data.get('preserve_columns', [])
            )
    
    def _on_start_processing(self):
        """Handle start processing - delegate to presenter."""
        if self.presenter:
            self.presenter.handle_start_processing()
    
    def _on_pause_processing(self):
        """Handle pause processing - delegate to presenter."""
        if self.presenter:
            self.presenter.handle_pause_processing()
    
    def _on_resume_processing(self):
        """Handle resume processing - delegate to presenter."""
        if self.presenter:
            self.presenter.handle_resume_processing()
    
    def _on_cancel_processing(self):
        """Handle cancel processing - delegate to presenter."""
        if self.presenter:
            self.presenter.handle_cancel_processing()
    
    def _on_export_file_selected(self, file_path: str):
        """Handle export file selection."""
        if self.presenter and self.results_df is not None:
            try:
                if self.presenter.export_results(file_path):
                    self._update_status(f"✅ Results exported to {file_path}")
                else:
                    self._update_status("❌ Export failed")
            except Exception as e:
                self._update_status(f"❌ Export error: {str(e)}")
    
    # View interface methods (called by presenter)
    
    def show_file_success(self, file_info: FileInfo):
        """Display successful file load."""
        self._update_status(f"✅ Loaded: {file_info.filename} ({file_info.row_count} rows, {len(file_info.columns)} columns)")
        
        # Show dependent UI sections
        if dpg.does_item_exist(self.preserve_columns_group_id):
            dpg.configure_item(self.preserve_columns_group_id, show=True)
        if dpg.does_item_exist(self.file_status_group_id):
            dpg.configure_item(self.file_status_group_id, show=True)
    
    def show_file_error(self, error_message: str):
        """Display file error."""
        self._update_status(f"❌ Error: {error_message}")
        
        # Hide dependent UI sections
        if dpg.does_item_exist(self.preserve_columns_group_id):
            dpg.configure_item(self.preserve_columns_group_id, show=False)
    
    def populate_columns(self, columns: list):
        """Populate column selector with available columns."""
        if self.column_selector:
            self.column_selector.populate_columns(columns)
    
    def suggest_url_column(self, column_name: str):
        """Suggest a URL column to the user."""
        # This could be enhanced to highlight the suggested column
        # For now, just update status
        self._update_status(f"💡 Suggested URL column: {column_name}")
    
    def set_processing_enabled(self, enabled: bool):
        """Enable or disable processing controls."""
        if self.processing_controls:
            self.processing_controls.set_start_enabled(enabled)
    
    def show_validation_success(self):
        """Show that validation passed."""
        self._update_status("✅ Ready to process")
    
    def show_validation_error(self, error_message: str):
        """Show validation error."""
        self._update_status(f"❌ Validation error: {error_message}")
    
    def show_processing_started(self):
        """Show that processing has started."""
        self._update_status("🔄 Processing started...")
        if self.processing_controls:
            self.processing_controls.set_processing_state(True, False)
    
    def show_processing_paused(self):
        """Show that processing is paused."""
        self._update_status("⏸ Processing paused")
        if self.processing_controls:
            self.processing_controls.set_processing_state(True, True)
    
    def show_processing_resumed(self):
        """Show that processing is resumed."""
        self._update_status("▶ Processing resumed")
        if self.processing_controls:
            self.processing_controls.set_processing_state(True, False)
    
    def show_processing_cancelled(self):
        """Show that processing was cancelled."""
        self._update_status("⏹ Processing cancelled")
        if self.processing_controls:
            self.processing_controls.set_processing_state(False, False)
        if self.progress_display:
            self.progress_display.reset()
    
    def show_processing_complete(self, result):
        """Show that processing completed."""
        if result.success:
            self._update_status(f"✅ Processing complete: {result.processed_count} URLs processed")
            self.results_df = result.dataframe
            if result.dataframe is not None:
                self._populate_results_table(result.dataframe)
        else:
            self._update_status(f"❌ Processing failed: {result.error_message}")
        
        if self.processing_controls:
            self.processing_controls.set_processing_state(False, False)
        if self.progress_display:
            self.progress_display.clear_latest_url()
    
    def show_processing_error(self, error_message: str):
        """Show processing error."""
        self._update_status(f"❌ Processing error: {error_message}")
        if self.processing_controls:
            self.processing_controls.set_processing_state(False, False)
        if self.progress_display:
            self.progress_display.clear_latest_url()
    
    def update_progress(self, status: ProcessingStatus):
        """Update progress display."""
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
            if status.current_action and status.current_action.startswith("Checking: "):
                url = status.current_action[10:]  # Remove "Checking: " prefix
                self.progress_display.update_latest_url(url)
    
    # Utility methods
    
    def _update_status(self, message: str):
        """Update file status display."""
        if dpg.does_item_exist(self.file_status_id):
            dpg.set_value(self.file_status_id, message)
    
    def _populate_results_table(self, results_df: pd.DataFrame):
        """Populate results table with data."""
        if not dpg.does_item_exist(self.results_table_id):
            return
        
        # Clear existing table content
        dpg.delete_item(self.results_table_id, children_only=True)
        
        # Re-add table columns
        dpg.add_table_column(label="URL", parent=self.results_table_id)
        dpg.add_table_column(label="Status", parent=self.results_table_id)
        dpg.add_table_column(label="Info", parent=self.results_table_id)
        
        # Add data rows (limit to first 100 for performance)
        max_rows = min(100, len(results_df))
        for i in range(max_rows):
            row = results_df.iloc[i]
            with dpg.table_row(parent=self.results_table_id):
                # URL (truncated if too long)
                url = str(row.get('url', ''))
                display_url = url[:50] + '...' if len(url) > 50 else url
                dpg.add_text(display_url)
                
                # Status
                status = str(row.get('status', 'Unknown'))
                dpg.add_text(status)
                
                # Info
                info = str(row.get('info', ''))
                display_info = info[:30] + '...' if len(info) > 30 else info
                dpg.add_text(display_info)
        
        # Add summary row if more than 100 results
        if len(results_df) > 100:
            with dpg.table_row(parent=self.results_table_id):
                dpg.add_text(f"... and {len(results_df) - 100} more results")
                dpg.add_text("")
                dpg.add_text("")
    
    def get_platform_display_name(self) -> str:
        """Get platform display name. Can be overridden by subclasses."""
        if self.presenter:
            return self.presenter.get_platform_display_name()
        return self.platform.title()
    
    def cleanup(self):
        """Clean up resources."""
        if self.presenter:
            self.presenter.cleanup()