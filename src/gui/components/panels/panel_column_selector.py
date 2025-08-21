import dearpygui.dearpygui as dpg
from typing import List, Set, Optional, Callable
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from ..widgets.dropdown_widget import Dropdown


class PanelPreserveColumns:
    """Component for selecting which CSV columns to preserve in output."""
    
    def __init__(self, parent_window: str, callback: Optional[Callable] = None):
        self.parent_window = parent_window
        self.callback = callback
        self.csv_columns: List[str] = []
        self.selected_columns: Set[str] = set()
        
        # UI element IDs
        self.container_id = "preserve_columns_container"
        self.post_dropdown: Optional[Dropdown] = None
        self.preserve_group_id = "preserve_columns_group"
        self.scroll_container_id = "preserve_scroll_container"
        
        # Checkbox IDs will be generated as needed
        self.checkbox_ids = {}
    
    def setup_ui(self):
        """Create the preserve columns UI."""
        with dpg.group(tag=self.container_id, parent=self.parent_window): 
            self.post_dropdown = Dropdown(
                parent_window=self.container_id,
                label="Post url (required)",
                placeholder="select post url column",
                callback=self._on_post_column_selected,
                id_suffix="_post_url"
            )
            self.post_dropdown.setup_ui()
            
            dpg.add_spacer(height=10)
            
            # Preserve columns section (hidden initially)
            with dpg.group(tag=self.preserve_group_id, show=False):
                dpg.add_text("Preserve columns", color=[255, 255, 255])
                dpg.add_spacer(height=5)
                
                # Scrollable container for checkboxes
                with dpg.child_window(
                    tag=self.scroll_container_id,
                    height=200,
                    border=True,
                    horizontal_scrollbar=False
                ):
                    dpg.add_text("Load a CSV file to see columns", color=[120, 120, 120])
    
    def populate_columns(self, csv_columns: List[str]):
        """Populate the component with CSV columns."""
        self.csv_columns = csv_columns
        
        # Populate post URL dropdown
        if self.post_dropdown:
            post_items = ["select post url column"] + csv_columns
            self.post_dropdown.populate_items(post_items)
        
        # Show preserve columns section
        if dpg.does_item_exist(self.preserve_group_id):
            dpg.configure_item(self.preserve_group_id, show=True)
        
        # Clear existing checkboxes
        if dpg.does_item_exist(self.scroll_container_id):
            dpg.delete_item(self.scroll_container_id, children_only=True)
        
        # Create checkboxes for each column
        self.checkbox_ids = {}
        self.selected_columns = set()
        
        with dpg.group(parent=self.scroll_container_id):
            for i, column in enumerate(csv_columns):
                checkbox_id = f"preserve_checkbox_{i}"
                self.checkbox_ids[column] = checkbox_id
                
                dpg.add_checkbox(
                    tag=checkbox_id,
                    label=column,
                    default_value=False,
                    user_data=column,
                    callback=lambda sender, value, user_data: self._on_checkbox_changed(user_data, value)
                )
                
                # Add small spacing between checkboxes
                if i < len(csv_columns) - 1:
                    dpg.add_spacer(height=2)
    
    def _on_post_column_selected(self, sender, value):
        """Handle post column selection."""
        if self.callback:
            try:
                self.callback('post_column_changed', {
                    'post_column': value,
                    'preserve_columns': list(self.selected_columns)
                })
            except Exception as e:
                print(f"Error in preserve columns callback: {e}")
    
    def _on_checkbox_changed(self, column: str, checked: bool):
        """Handle checkbox state change."""
        if checked:
            self.selected_columns.add(column)
        else:
            self.selected_columns.discard(column)
        
        # Notify callback
        if self.callback:
            try:
                self.callback('preserve_columns_changed', {
                    'post_column': self.get_post_column(),
                    'preserve_columns': list(self.selected_columns)
                })
            except Exception as e:
                print(f"Error in preserve columns callback: {e}")
    
    def get_post_column(self) -> str:
        """Get the selected post column."""
        if self.post_dropdown:
            value = self.post_dropdown.get_selected_value()
            if value and value != "select post url column":
                return value
        return ""
    
    def get_preserve_columns(self) -> List[str]:
        """Get the list of selected preserve columns."""
        return list(self.selected_columns)
    
    def get_all_selected_columns(self) -> dict:
        """Get both post column and preserve columns."""
        return {
            'post_column': self.get_post_column(),
            'preserve_columns': self.get_preserve_columns()
        }
    
    def clear_selections(self):
        """Clear all selections."""
        # Clear post dropdown
        if self.post_dropdown:
            self.post_dropdown.clear_selection()
        
        # Clear all checkboxes
        for column, checkbox_id in self.checkbox_ids.items():
            if dpg.does_item_exist(checkbox_id):
                dpg.set_value(checkbox_id, False)
        
        self.selected_columns.clear()
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the component."""
        # Enable/disable post dropdown
        if self.post_dropdown:
            self.post_dropdown.set_enabled(enabled)
        
        # Enable/disable all checkboxes
        for checkbox_id in self.checkbox_ids.values():
            if dpg.does_item_exist(checkbox_id):
                dpg.configure_item(checkbox_id, enabled=enabled)
    
    def validate(self) -> tuple[bool, str]:
        """Validate that post column is selected."""
        post_column = self.get_post_column()
        if not post_column:
            return False, "Post URL column must be selected"
        
        if post_column not in self.csv_columns:
            return False, f"Selected post column '{post_column}' not found in CSV"
        
        return True, "Validation passed"
