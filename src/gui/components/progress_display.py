import dearpygui.dearpygui as dpg
from typing import Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.state_manager import ProcessingState


class ProgressDisplay:
    """Component for displaying real-time processing progress."""
    
    def __init__(self, parent_window: str):
        self.parent_window = parent_window
        
        # UI element IDs
        self.group_id = "progress_display_group"
        self.status_text_id = "progress_status_text"
        self.current_action_id = "progress_current_action"
        self.stats_text_id = "progress_stats_text"
        self.progress_bar_id = "progress_bar"
        
        # Current state
        self.current_state = ProcessingState.IDLE
        self.progress_data = {
            'current': 0,
            'total': 0,
            'stats': {'live': 0, 'removed': 0, 'restricted': 0, 'errors': 0},
            'current_action': ''
        }
    
    def setup_ui(self):
        """Create the progress display UI."""
        with dpg.group(tag=self.group_id, parent=self.parent_window):
            # Status text
            dpg.add_text(
                tag=self.status_text_id,
                default_value="Ready",
                color=[100, 255, 100]
            )
            
            dpg.add_spacer(height=5)
            
            # Progress bar
            dpg.add_progress_bar(
                tag=self.progress_bar_id,
                default_value=0.0,
                width=400,
                height=20,
                show=False  # Hidden initially
            )
            
            dpg.add_spacer(height=5)
            
            # Current action
            dpg.add_text(
                tag=self.current_action_id,
                default_value="",
                color=[180, 180, 180],
                show=False  # Hidden initially
            )
            
            dpg.add_spacer(height=5)
            
            # Stats display
            dpg.add_text(
                tag=self.stats_text_id,
                default_value="",
                color=[200, 200, 255],
                show=False  # Hidden initially
            )
    
    def update_progress(self, state: ProcessingState, data: Dict):
        """Update the progress display with new state and data."""
        self.current_state = state
        self.progress_data.update(data)
        
        # Update status text
        status_colors = {
            ProcessingState.IDLE: [100, 255, 100],
            ProcessingState.LOADING_CSV: [255, 255, 100],
            ProcessingState.VALIDATING_DATA: [255, 255, 100],
            ProcessingState.INITIALIZING_SCRAPERS: [255, 255, 100],
            ProcessingState.PROCESSING_URLS: [100, 255, 255],
            ProcessingState.FINALIZING_RESULTS: [255, 255, 100],
            ProcessingState.COMPLETED: [100, 255, 100],
            ProcessingState.ERROR: [255, 100, 100],
            ProcessingState.CANCELLED: [255, 255, 100]
        }
        
        color = status_colors.get(state, [255, 255, 255])
        
        # Format status text with progress info
        if state == ProcessingState.PROCESSING_URLS and data.get('total', 0) > 0:
            current = data.get('current', 0)
            total = data.get('total', 0)
            status_text = f"{state.value} ({current}/{total})"
        else:
            status_text = state.value
        
        if dpg.does_item_exist(self.status_text_id):
            dpg.set_value(self.status_text_id, status_text)
            dpg.configure_item(self.status_text_id, color=color)
        
        # Update progress bar
        if state == ProcessingState.PROCESSING_URLS:
            self._show_progress_elements(True)
            self._update_progress_bar(data)
            self._update_current_action(data)
            self._update_stats(data)
        elif state in [ProcessingState.COMPLETED, ProcessingState.ERROR, ProcessingState.CANCELLED]:
            self._show_progress_elements(False)
        elif state != ProcessingState.IDLE:
            self._show_progress_elements(True, show_stats=False)
    
    def _show_progress_elements(self, show: bool, show_stats: bool = True):
        """Show or hide progress-related elements."""
        elements = [self.progress_bar_id, self.current_action_id]
        if show_stats:
            elements.append(self.stats_text_id)
        
        for element_id in elements:
            if dpg.does_item_exist(element_id):
                dpg.configure_item(element_id, show=show)
    
    def _update_progress_bar(self, data: Dict):
        """Update the progress bar value."""
        current = data.get('current', 0)
        total = data.get('total', 1)
        progress = current / total if total > 0 else 0.0
        
        if dpg.does_item_exist(self.progress_bar_id):
            dpg.set_value(self.progress_bar_id, progress)
    
    def _update_current_action(self, data: Dict):
        """Update the current action text."""
        action = data.get('current_action', '')
        if dpg.does_item_exist(self.current_action_id):
            dpg.set_value(self.current_action_id, action)
    
    def _update_stats(self, data: Dict):
        """Update the processing statistics."""
        stats = data.get('stats', {})
        
        stats_text = (
            f"Live: {stats.get('live', 0)}    "
            f"Removed: {stats.get('removed', 0)}    "
            f"Restricted: {stats.get('restricted', 0)}    "
            f"Errors: {stats.get('errors', 0)}"
        )
        
        if dpg.does_item_exist(self.stats_text_id):
            dpg.set_value(self.stats_text_id, stats_text)
    
    def reset(self):
        """Reset the progress display to initial state."""
        self.current_state = ProcessingState.IDLE
        self.progress_data = {
            'current': 0,
            'total': 0,
            'stats': {'live': 0, 'removed': 0, 'restricted': 0, 'errors': 0},
            'current_action': ''
        }
        
        if dpg.does_item_exist(self.status_text_id):
            dpg.set_value(self.status_text_id, "Ready")
            dpg.configure_item(self.status_text_id, color=[100, 255, 100])
        
        self._show_progress_elements(False)