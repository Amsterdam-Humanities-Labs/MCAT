import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional, Callable
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import config
from .dropdown import Dropdown


class ColumnMapper:
    """4-column mapping component for CSV files."""
    
    def __init__(self, parent_window: str, platform: str = "youtube", callback: Optional[Callable] = None):
        self.parent_window = parent_window
        self.platform = platform
        self.callback = callback
        self.csv_columns: List[str] = []
        
        # Get expected columns from config
        self.expected_columns = config.get_platform_columns(platform)
        
        # UI element IDs
        self.group_id = "column_mapper_group"
        
        # Dropdown components
        self.post_dropdown: Optional[Dropdown] = None
        self.date_dropdown: Optional[Dropdown] = None
        self.engagement_dropdown: Optional[Dropdown] = None
        self.user_dropdown: Optional[Dropdown] = None
        
        # Current selections
        self.selections = {
            'post': '',
            'date': '',
            'engagement': '',
            'user': ''
        }
    
    def setup_ui(self):
        """Create the column mapping UI components."""
        with dpg.group(tag=self.group_id, parent=self.parent_window):
            
            # Post Column (Required)
            self.post_dropdown = Dropdown(
                parent_window=self.group_id,
                label="Post url (required)",
                placeholder="select post url column",
                callback=lambda s, v: self._on_column_selected('post', v),
                id_suffix="_post"
            )
            self.post_dropdown.setup_ui()
            
            dpg.add_spacer(height=5)  # Reduced spacing
            
            # Date Column (Optional)
            self.date_dropdown = Dropdown(
                parent_window=self.group_id,
                label="Date",
                placeholder="select post date column",
                callback=lambda s, v: self._on_column_selected('date', v),
                id_suffix="_date"
            )
            self.date_dropdown.setup_ui()
            
            dpg.add_spacer(height=5)  # Reduced spacing
            
            # Engagement Column (Optional)
            self.engagement_dropdown = Dropdown(
                parent_window=self.group_id,
                label="Engagement",
                placeholder="select engagement column",
                callback=lambda s, v: self._on_column_selected('engagement', v),
                id_suffix="_engagement"
            )
            self.engagement_dropdown.setup_ui()
            
            dpg.add_spacer(height=5)  # Reduced spacing
            
            # User Column (Optional)
            self.user_dropdown = Dropdown(
                parent_window=self.group_id,
                label="User",
                placeholder="select user column",
                callback=lambda s, v: self._on_column_selected('user', v),
                id_suffix="_user"
            )
            self.user_dropdown.setup_ui()
    
    def populate_dropdowns(self, csv_columns: List[str]):
        """Populate dropdowns with CSV column names."""
        self.csv_columns = csv_columns
        
        # Add a "none" option and then CSV columns
        items = ["[none]"] + csv_columns
        
        # Update all dropdown components
        if self.post_dropdown:
            self.post_dropdown.populate_items(items)
        
        if self.date_dropdown:
            self.date_dropdown.populate_items(items)
        
        if self.engagement_dropdown:
            self.engagement_dropdown.populate_items(items)
        
        if self.user_dropdown:
            self.user_dropdown.populate_items(items)
        
        # Try to auto-match columns based on expected names
        self._auto_match_columns()
    
    def _auto_match_columns(self):
        """Attempt to automatically match CSV columns to expected columns."""
        for col_type, expected_name in self.expected_columns.items():
            # Look for exact match first
            if expected_name in self.csv_columns:
                self._set_column_selection(col_type, expected_name)
                continue
            
            # Look for case-insensitive match
            for csv_col in self.csv_columns:
                if csv_col.lower() == expected_name.lower():
                    self._set_column_selection(col_type, csv_col)
                    break
    
    def _set_column_selection(self, col_type: str, column_name: str):
        """Set the selection for a specific column type."""
        dropdown = getattr(self, f"{col_type}_dropdown", None)
        if dropdown:
            dropdown.set_selected_value(column_name)
            self.selections[col_type] = column_name
            
            # Trigger callback to update validation
            if self.callback:
                try:
                    self.callback(col_type, column_name, self.get_column_mapping())
                except Exception as e:
                    print(f"Error in auto-match callback: {e}")
    
    def _on_column_selected(self, col_type: str, selected_value: str):
        """Handle column selection change."""
        if selected_value == "Select CSV column...":
            self.selections[col_type] = ''
        else:
            self.selections[col_type] = selected_value
        
        # Notify callback if provided
        if self.callback:
            try:
                self.callback(col_type, selected_value, self.get_column_mapping())
            except Exception as e:
                print(f"Error in column mapper callback: {e}")
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Get the current column mapping."""
        return {k: v for k, v in self.selections.items() if v}
    
    def validate_mapping(self) -> tuple[bool, str]:
        """Validate that all columns are mapped."""
        print(f"DEBUG: Current selections: {self.selections}")  # Debug
        print(f"DEBUG: Available CSV columns: {self.csv_columns}")  # Debug
        
        # All columns are required now
        for col_type in ['post', 'date', 'engagement', 'user']:
            if not self.selections.get(col_type):
                print(f"DEBUG: Missing {col_type} column")  # Debug
                return False, f"{col_type.title()} column must be selected"
        
        # Check that selected columns exist in CSV
        for col_type, selected_col in self.selections.items():
            if selected_col and selected_col not in self.csv_columns:
                print(f"DEBUG: Column {selected_col} not found in CSV")  # Debug
                return False, f"Selected {col_type} column '{selected_col}' not found in CSV"
        
        print("DEBUG: Validation passed!")  # Debug
        return True, "All columns mapped successfully"
    
    def clear_selections(self):
        """Clear all column selections."""
        self.selections = {k: '' for k in self.selections.keys()}
        
        # Reset dropdown values
        if self.post_dropdown:
            self.post_dropdown.clear_selection()
        if self.date_dropdown:
            self.date_dropdown.clear_selection()
        if self.engagement_dropdown:
            self.engagement_dropdown.clear_selection()
        if self.user_dropdown:
            self.user_dropdown.clear_selection()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable all dropdowns."""
        if self.post_dropdown:
            self.post_dropdown.set_enabled(enabled)
        if self.date_dropdown:
            self.date_dropdown.set_enabled(enabled)
        if self.engagement_dropdown:
            self.engagement_dropdown.set_enabled(enabled)
        if self.user_dropdown:
            self.user_dropdown.set_enabled(enabled)