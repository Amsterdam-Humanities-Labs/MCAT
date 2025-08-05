import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional, Callable
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import config


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
        self.post_combo_id = "post_column_combo"
        self.date_combo_id = "date_column_combo"
        self.engagement_combo_id = "engagement_column_combo"
        self.user_combo_id = "user_column_combo"
        
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
            dpg.add_text("Column Mapping:", color=[200, 200, 255])
            dpg.add_spacer()
            
            # Post Column (Required)
            with dpg.group(horizontal=True):
                dpg.add_text("Post Column:", color=[200, 200, 255])
                dpg.add_combo(
                    tag=self.post_combo_id,
                    items=["Select CSV column..."],
                    default_value="Select CSV column...",
                    width=200,
                    callback=lambda s, v: self._on_column_selected('post', v)
                )
            
            dpg.add_spacer(height=2)
            
            # Date Column (Optional)
            with dpg.group(horizontal=True):
                dpg.add_text("Date Column:", color=[200, 200, 255])
                dpg.add_combo(
                    tag=self.date_combo_id,
                    items=["Select CSV column..."],
                    default_value="Select CSV column...",
                    width=200,
                    callback=lambda s, v: self._on_column_selected('date', v)
                )
            
            dpg.add_spacer(height=2)
            
            # Engagement Column (Optional)
            with dpg.group(horizontal=True):
                dpg.add_text("Engagement Column:", color=[200, 200, 255])
                dpg.add_combo(
                    tag=self.engagement_combo_id,
                    items=["Select CSV column..."],
                    default_value="Select CSV column...",
                    width=200,
                    callback=lambda s, v: self._on_column_selected('engagement', v)
                )
            
            dpg.add_spacer(height=2)
            
            # User Column (Optional)
            with dpg.group(horizontal=True):
                dpg.add_text("User Column:", color=[200, 200, 255])
                dpg.add_combo(
                    tag=self.user_combo_id,
                    items=["Select CSV column..."],
                    default_value="Select CSV column...",
                    width=200,
                    callback=lambda s, v: self._on_column_selected('user', v)
                )
    
    def populate_dropdowns(self, csv_columns: List[str]):
        """Populate dropdowns with CSV column names."""
        self.csv_columns = csv_columns
        
        # All columns are required now
        dropdown_items = ["Select CSV column..."] + csv_columns
        
        # Update all dropdowns
        for combo_id in [self.post_combo_id, self.date_combo_id, self.engagement_combo_id, self.user_combo_id]:
            if dpg.does_item_exist(combo_id):
                dpg.configure_item(combo_id, items=dropdown_items)
        
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
        combo_id = getattr(self, f"{col_type}_combo_id")
        if dpg.does_item_exist(combo_id):
            dpg.set_value(combo_id, column_name)
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
        
        # Reset dropdowns to default
        for col_type in ['post', 'date', 'engagement', 'user']:
            combo_id = getattr(self, f"{col_type}_combo_id")
            if dpg.does_item_exist(combo_id):
                dpg.set_value(combo_id, "Select CSV column...")
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the column mapper."""
        for col_type in ['post', 'date', 'engagement', 'user']:
            combo_id = getattr(self, f"{col_type}_combo_id")
            if dpg.does_item_exist(combo_id):
                dpg.configure_item(combo_id, enabled=enabled)