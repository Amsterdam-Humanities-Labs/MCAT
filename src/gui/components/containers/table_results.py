import dearpygui.dearpygui as dpg
import pandas as pd
from typing import Optional, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))


class ResultsTable:
    """Component for displaying processing results in a table format."""
    
    def __init__(self, parent_window: str):
        self.parent_window = parent_window
        self.current_df: Optional[pd.DataFrame] = None
        
        # UI element IDs
        self.group_id = "results_table_group"
        self.table_id = "results_table"
        self.info_text_id = "results_info_text"
        
        # Display settings
        self.max_display_rows = 100  # Limit for performance
        self.result_columns = ['url', 'status', 'info', 'timestamp', 'error_message']
    
    def setup_ui(self):
        """Create the results table UI."""
        with dpg.group(tag=self.group_id, parent=self.parent_window):
            # Info text
            dpg.add_text(
                tag=self.info_text_id,
                default_value="Results will appear here after processing",
                color=[180, 180, 180]
            )
            
            dpg.add_spacer(height=5)
            
            # Results table (will be created dynamically)
            with dpg.child_window(
                tag=self.table_id,
                height=300,
                border=True,
                horizontal_scrollbar=True
            ):
                dpg.add_text("Load and process a CSV file to see results", color=[120, 120, 120])
    
    def update_results(self, df: pd.DataFrame):
        """Update the table with new results."""
        self.current_df = df.copy()
        self._refresh_table()
    
    def _refresh_table(self):
        """Refresh the table display with current data."""
        if self.current_df is None:
            return
        
        # Clear existing table content
        if dpg.does_item_exist(self.table_id):
            dpg.delete_item(self.table_id, children_only=True)
        
        # Update info text
        total_rows = len(self.current_df)
        display_rows = min(total_rows, self.max_display_rows)
        
        info_text = f"Showing {display_rows} of {total_rows} results"
        if total_rows > self.max_display_rows:
            info_text += f" (limited for performance)"
        
        if dpg.does_item_exist(self.info_text_id):
            dpg.set_value(self.info_text_id, info_text)
            dpg.configure_item(self.info_text_id, color=[200, 200, 255])
        
        # Create table
        self._create_table_content()
    
    def _create_table_content(self):
        """Create the actual table content."""
        if self.current_df is None or self.current_df.empty:
            dpg.add_text("No results to display", 
                        color=[120, 120, 120], 
                        parent=self.table_id)
            return
        
        # Limit rows for performance
        display_df = self.current_df.head(self.max_display_rows)
        
        # Get relevant columns (preserve original + add result columns)
        display_columns = []
        
        # Add original CSV columns that have data
        for col in display_df.columns:
            if col not in self.result_columns and not display_df[col].isna().all():
                display_columns.append(col)
        
        # Add result columns
        for col in self.result_columns:
            if col in display_df.columns:
                display_columns.append(col)
        
        if not display_columns:
            dpg.add_text("No columns to display", 
                        color=[120, 120, 120], 
                        parent=self.table_id)
            return
        
        # Create table with dpg.table
        with dpg.table(
            header_row=True,
            resizable=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True,
            parent=self.table_id
        ):
            # Add columns
            for col in display_columns:
                dpg.add_table_column(label=col, width_fixed=True, init_width_or_weight=150)
            
            # Add rows
            for _, row in display_df.iterrows():
                with dpg.table_row():
                    for col in display_columns:
                        value = str(row.get(col, ''))
                        
                        # Truncate long values
                        if len(value) > 50:
                            value = value[:47] + "..."
                        
                        # Color code status column
                        if col == 'status':
                            color = self._get_status_color(value)
                            dpg.add_text(value, color=color)
                        else:
                            dpg.add_text(value)
    
    def _get_status_color(self, status: str) -> List[int]:
        """Get color for status text based on status value."""
        status_colors = {
            'Live': [100, 255, 100],           # Green
            'Removed': [255, 100, 100],        # Red
            'Age-restricted': [255, 200, 100],  # Orange
            'Geo-blocked': [255, 200, 100],     # Orange
            'Private': [255, 200, 100],         # Orange
            'Restricted': [255, 255, 100],      # Yellow
            'Error': [255, 100, 100],           # Red
        }
        return status_colors.get(status, [200, 200, 200])  # Default gray
    
    def clear_results(self):
        """Clear the results table."""
        self.current_df = None
        
        if dpg.does_item_exist(self.table_id):
            dpg.delete_item(self.table_id, children_only=True)
            dpg.add_text("Load and process a CSV file to see results", 
                        color=[120, 120, 120], 
                        parent=self.table_id)
        
        if dpg.does_item_exist(self.info_text_id):
            dpg.set_value(self.info_text_id, "Results will appear here after processing")
            dpg.configure_item(self.info_text_id, color=[180, 180, 180])
    
    def get_results(self) -> Optional[pd.DataFrame]:
        """Get the current results DataFrame."""
        return self.current_df