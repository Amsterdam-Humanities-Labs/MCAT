import dearpygui.dearpygui as dpg
from typing import Optional, Callable
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))


class ExportPanel:
    """Component for exporting processing results."""
    
    def __init__(self, parent_window: str, export_callback: Optional[Callable] = None):
        self.parent_window = parent_window
        self.export_callback = export_callback
        self.results_df: Optional[pd.DataFrame] = None
        
        # UI element IDs
        self.group_id = "export_panel_group"
        self.export_button_id = "export_button"
        self.file_dialog_id = "export_file_dialog"
        self.status_text_id = "export_status_text"
    
    def setup_ui(self):
        """Create the export panel UI."""
        with dpg.group(tag=self.group_id, parent=self.parent_window):
            dpg.add_text("Export Results:", color=[200, 200, 255])
            dpg.add_spacer(height=5)
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    tag=self.export_button_id,
                    label="Export to CSV",
                    callback=self._show_export_dialog,
                    enabled=False  # Disabled until results are available
                )
                
                dpg.add_text(
                    tag=self.status_text_id,
                    default_value="No results to export",
                    color=[180, 180, 180]
                )
            
            # File dialog for export (hidden by default)
            with dpg.file_dialog(
                tag=self.file_dialog_id,
                directory_selector=False,
                show=False,
                callback=self._export_file_selected,
                cancel_callback=self._export_dialog_cancelled,
                width=700,
                height=400,
                modal=True,
                default_filename="mcat_results.csv"
            ):
                dpg.add_file_extension(".csv", color=(255, 255, 0, 255))
    
    def set_results(self, df: pd.DataFrame):
        """Set the results DataFrame for export."""
        self.results_df = df.copy() if df is not None else None
        self._update_export_status()
    
    def _update_export_status(self):
        """Update the export status and button state."""
        if self.results_df is None or self.results_df.empty:
            status_text = "No results to export"
            status_color = [180, 180, 180]
            button_enabled = False
        else:
            row_count = len(self.results_df)
            status_text = f"Ready to export {row_count} results"
            status_color = [100, 255, 100]
            button_enabled = True
        
        if dpg.does_item_exist(self.status_text_id):
            dpg.set_value(self.status_text_id, status_text)
            dpg.configure_item(self.status_text_id, color=status_color)
        
        if dpg.does_item_exist(self.export_button_id):
            dpg.configure_item(self.export_button_id, enabled=button_enabled)
    
    def _show_export_dialog(self):
        """Show the file export dialog."""
        if self.results_df is None:
            return
        
        dpg.show_item(self.file_dialog_id)
    
    def _export_file_selected(self, sender, app_data):
        """Handle export file selection."""
        file_path = app_data['file_path_name']
        
        try:
            # Ensure .csv extension
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            
            # Perform export
            if self.export_callback:
                success = self.export_callback(file_path)
                if success:
                    self._show_export_success(file_path)
                else:
                    self._show_export_error("Export failed")
            else:
                # Fallback: direct export
                self.results_df.to_csv(file_path, index=False)
                self._show_export_success(file_path)
                
        except Exception as e:
            self._show_export_error(str(e))
    
    def _export_dialog_cancelled(self):
        """Handle export dialog cancellation."""
        pass  # Do nothing when cancelled
    
    def _show_export_success(self, file_path: str):
        """Show export success message."""
        filename = os.path.basename(file_path)
        status_text = f" Exported to {filename}"
        
        if dpg.does_item_exist(self.status_text_id):
            dpg.set_value(self.status_text_id, status_text)
            dpg.configure_item(self.status_text_id, color=[100, 255, 100])
    
    def _show_export_error(self, error_message: str):
        """Show export error message."""
        status_text = f"L Export failed: {error_message}"
        
        if dpg.does_item_exist(self.status_text_id):
            dpg.set_value(self.status_text_id, status_text)
            dpg.configure_item(self.status_text_id, color=[255, 100, 100])
    
    def clear_results(self):
        """Clear results and reset export panel."""
        self.results_df = None
        self._update_export_status()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the export panel."""
        if dpg.does_item_exist(self.export_button_id):
            dpg.configure_item(self.export_button_id, enabled=enabled and self.results_df is not None)