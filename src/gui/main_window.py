import dearpygui.dearpygui as dpg
import pandas as pd
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from utils.csv_handler import CSVHandler
from utils.state_manager import StateManager, ProcessingState
from gui.components.platform_tabs import PlatformTabs
from gui.processing_controller import ProcessingController


class MainWindow:
    """Primary GUI controller using Dear PyGui."""
    
    def __init__(self):
        self.state_manager = StateManager()
        self.platform_tabs: Optional[PlatformTabs] = None
        self.processing_controller: Optional[ProcessingController] = None
        
        # UI element IDs
        self.main_window_id = "main_window"
        self.status_text_id = "status_text"
        
        # Initialize processing controller
        self.processing_controller = ProcessingController(self.state_manager)
        self.processing_controller.set_callbacks(
            on_processing_complete=self._on_processing_complete,
            on_processing_error=self._on_processing_error
        )
        
        # Subscribe to state changes
        self.state_manager.subscribe(self._on_state_changed)
    
    def setup_ui(self):
        """Create the main window UI."""
        # Create main window
        with dpg.window(
            tag=self.main_window_id,
            label="",
            width=1000,
            height=800,
            pos=[50, 50]
        ):

            # Load larger font for 4K display
            with dpg.font_registry():
                font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       "assets", "fonts", "NotoSans-Medium.ttf")
                large_font = dpg.add_font(font_path, 22)  # 20px for 4K, adjust as needed
            
            dpg.bind_font(large_font)
 
            # Platform Tabs
            self.platform_tabs = PlatformTabs(
                parent_window=self.main_window_id,
                state_manager=self.state_manager,
                processing_controller=self.processing_controller
            )
            self.platform_tabs.setup_ui()
            
    
    def run(self):
        """Start the GUI application."""
        dpg.create_context()
        dpg.create_viewport(title="MCAT Content Moderation Checker", width=1050, height=850)
        
        self.setup_ui()
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.main_window_id, True)
        
        try:
            dpg.start_dearpygui()
        finally:
            # Cleanup components
            if self.platform_tabs:
                self.platform_tabs.cleanup()
            if self.processing_controller:
                self.processing_controller.cleanup()
            dpg.destroy_context()
    
    
    
    
    def _update_status(self, message: str, color: list = None):
        """Update the status display."""
        dpg.set_value(self.status_text_id, message)
        if color:
            dpg.configure_item(self.status_text_id, color=color)
    
    
    
    
    def _on_state_changed(self, state: ProcessingState, data: dict):
        """Handle state manager updates."""
        status_colors = {
            ProcessingState.IDLE: [100, 255, 100],
            ProcessingState.LOADING_CSV: [255, 255, 100],
            ProcessingState.ERROR: [255, 100, 100],
            ProcessingState.COMPLETED: [100, 255, 100]
        }
        
        color = status_colors.get(state, [255, 255, 255])
        self._update_status(state.value, color)
    
    
    
    
    
    def _on_processing_complete(self, result):
        """Handle processing completion."""
        # Delegate to YouTube tab
        if self.platform_tabs and self.platform_tabs.get_youtube_tab():
            self.platform_tabs.get_youtube_tab().update_processing_results(result)
        
        self._update_status(f"Processing completed! {result.processed_count} URLs processed", [100, 255, 100])
    
    def _on_processing_error(self, error_message: str):
        """Handle processing error."""
        # Delegate to YouTube tab
        if self.platform_tabs and self.platform_tabs.get_youtube_tab():
            self.platform_tabs.get_youtube_tab().handle_processing_error(error_message)
        
        self._update_status(f"Processing error: {error_message}", [255, 100, 100])
    
    
    def _on_state_changed(self, state: ProcessingState, data: dict):
        """Handle state manager updates."""
        # Update main status
        status_colors = {
            ProcessingState.IDLE: [100, 255, 100],
            ProcessingState.LOADING_CSV: [255, 255, 100],
            ProcessingState.ERROR: [255, 100, 100],
            ProcessingState.COMPLETED: [100, 255, 100]
        }
        
        color = status_colors.get(state, [255, 255, 255])
        if state not in [ProcessingState.PROCESSING_URLS]:  # Don't override processing status
            self._update_status(state.value, color)
