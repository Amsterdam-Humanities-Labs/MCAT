import dearpygui.dearpygui as dpg
from typing import Optional, Callable
from enum import Enum


class ControlState(Enum):
    """Processing control states for the UI component."""
    IDLE = "idle"
    PROCESSING = "processing"
    PAUSED = "paused"


class ProcessingControls:
    """Dedicated component for processing control buttons (start/pause/cancel)."""
    
    def __init__(self, parent_window: str):
        self.parent_window = parent_window
        self.state = ControlState.IDLE
        
        # Callbacks
        self.on_start_callback: Optional[Callable] = None
        self.on_pause_callback: Optional[Callable] = None
        self.on_resume_callback: Optional[Callable] = None
        self.on_cancel_callback: Optional[Callable] = None
        
        # UI element IDs
        self.container_id = f"processing_controls_{id(self)}"
        self.start_button_id = f"start_button_{id(self)}"
        self.pause_button_id = f"pause_button_{id(self)}"
        self.cancel_button_id = f"cancel_button_{id(self)}"
    
    def setup_ui(self, start_label: str = "Start Processing"):
        """Create the processing control buttons."""
        with dpg.group(tag=self.container_id, parent=self.parent_window):
            # Start/Processing button
            dpg.add_button(
                tag=self.start_button_id,
                label=start_label,
                callback=self._on_start_clicked,
                enabled=False,
                width=-1
            )
            
            # Pause button (hidden initially)
            dpg.add_button(
                tag=self.pause_button_id,
                label="⏸ Pause",
                callback=self._on_pause_clicked,
                show=False,
                width=-1
            )
            
            dpg.add_spacer(height=5)
            
            # Cancel button (always visible but disabled when not processing)
            dpg.add_button(
                tag=self.cancel_button_id,
                label="Cancel",
                callback=self._on_cancel_clicked,
                enabled=False,
                width=-1
            )
    
    def set_callbacks(self, 
                     on_start: Callable = None,
                     on_pause: Callable = None, 
                     on_resume: Callable = None,
                     on_cancel: Callable = None):
        """Set callback functions for control events."""
        self.on_start_callback = on_start
        self.on_pause_callback = on_pause
        self.on_resume_callback = on_resume
        self.on_cancel_callback = on_cancel
    
    def set_start_enabled(self, enabled: bool):
        """Enable/disable the start button."""
        if dpg.does_item_exist(self.start_button_id):
            dpg.configure_item(self.start_button_id, enabled=enabled)
    
    def set_processing_state(self, processing: bool, paused: bool = False):
        """Update UI based on processing state."""
        if processing:
            if paused:
                self.state = ControlState.PAUSED
                # Show resume button
                if dpg.does_item_exist(self.pause_button_id):
                    dpg.configure_item(self.pause_button_id, label="▶ Resume")
            else:
                self.state = ControlState.PROCESSING
                # Show pause button
                if dpg.does_item_exist(self.pause_button_id):
                    dpg.configure_item(self.pause_button_id, label="⏸ Pause")
            
            # Hide start, show pause, enable cancel
            if dpg.does_item_exist(self.start_button_id):
                dpg.configure_item(self.start_button_id, show=False)
            if dpg.does_item_exist(self.pause_button_id):
                dpg.configure_item(self.pause_button_id, show=True)
            if dpg.does_item_exist(self.cancel_button_id):
                dpg.configure_item(self.cancel_button_id, enabled=True)
        else:
            self.state = ControlState.IDLE
            # Show start, hide pause, disable cancel
            if dpg.does_item_exist(self.start_button_id):
                dpg.configure_item(self.start_button_id, show=True)
            if dpg.does_item_exist(self.pause_button_id):
                dpg.configure_item(self.pause_button_id, show=False)
            if dpg.does_item_exist(self.cancel_button_id):
                dpg.configure_item(self.cancel_button_id, enabled=False)
    
    def _on_start_clicked(self):
        """Handle start button click."""
        if self.on_start_callback:
            self.on_start_callback()
    
    def _on_pause_clicked(self):
        """Handle pause/resume button click."""
        if self.state == ControlState.PROCESSING:
            if self.on_pause_callback:
                self.on_pause_callback()
        elif self.state == ControlState.PAUSED:
            if self.on_resume_callback:
                self.on_resume_callback()
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.on_cancel_callback:
            self.on_cancel_callback()
    
    def set_enabled(self, enabled: bool):
        """Enable/disable the entire control component."""
        if dpg.does_item_exist(self.container_id):
            # Enable/disable all buttons except those with specific state logic
            if dpg.does_item_exist(self.start_button_id):
                dpg.configure_item(self.start_button_id, enabled=enabled and self.state == ProcessingState.IDLE)
            if dpg.does_item_exist(self.pause_button_id):
                dpg.configure_item(self.pause_button_id, enabled=enabled)