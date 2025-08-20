import dearpygui.dearpygui as dpg
from typing import Callable, Optional, List
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))


class Dropdown:
    """Reusable dropdown component with label and dynamic width."""
    
    def __init__(self, parent_window: str, label: str, placeholder: str, 
                 callback: Optional[Callable] = None, id_suffix: str = ""):
        self.parent_window = parent_window
        self.label = label
        self.placeholder = placeholder
        self.callback = callback
        self.id_suffix = id_suffix
        
        # UI element IDs
        self.group_id = f"dropdown_group{id_suffix}"
        self.combo_id = f"dropdown_combo{id_suffix}"
        
        # State
        self.items = [placeholder]
        self.selected_value = placeholder
    
    def setup_ui(self):
        """Create the dropdown UI components with label above."""
        with dpg.group(tag=self.group_id, parent=self.parent_window):
            # Label above dropdown
            dpg.add_text(self.label, color=[255, 255, 255])
            
            # Dropdown with dynamic width (-1 fills available width)
            dpg.add_combo(
                tag=self.combo_id,
                items=self.items,
                default_value=self.placeholder,
                width=-1,  # This fills the available width (like CSS width: 100%)
                callback=self._on_selection_changed
            )
    
    def _on_selection_changed(self, sender, value):
        """Handle dropdown selection changes."""
        self.selected_value = value
        if self.callback:
            try:
                self.callback(sender, value)
            except Exception as e:
                print(f"Error in dropdown callback: {e}")
    
    def populate_items(self, items: List[str]):
        """Update dropdown with new items."""
        self.items = items
        if dpg.does_item_exist(self.combo_id):
            dpg.configure_item(self.combo_id, items=items)
    
    def set_selected_value(self, value: str):
        """Set the selected value."""
        self.selected_value = value
        if dpg.does_item_exist(self.combo_id):
            dpg.set_value(self.combo_id, value)
    
    def get_selected_value(self) -> str:
        """Get the currently selected value."""
        return self.selected_value
    
    def clear_selection(self):
        """Clear selection back to placeholder."""
        self.selected_value = self.placeholder
        if dpg.does_item_exist(self.combo_id):
            dpg.set_value(self.combo_id, self.placeholder)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the dropdown."""
        if dpg.does_item_exist(self.combo_id):
            dpg.configure_item(self.combo_id, enabled=enabled)