import dearpygui.dearpygui as dpg
import pandas as pd
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from utils.csv_handler import CSVHandler
from gui.components.containers.tab_container_platforms import PlatformTabs
from gui.processing_controller import ProcessingController
from gui.theme import AppTheme


class MainWindow:
    """Primary GUI controller using Dear PyGui."""
    
    def __init__(self):
        self.platform_tabs: Optional[PlatformTabs] = None
        self.processing_controller: Optional[ProcessingController] = None
        
        # UI element IDs
        self.main_window_id = "main_window"
        
        # Initialize processing controller
        self.processing_controller = ProcessingController()
        self.processing_controller.set_callbacks(
            on_processing_complete=self._on_processing_complete,
            on_processing_error=self._on_processing_error,
            on_progress_update=self._on_progress_update
        )
    
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
                processing_controller=self.processing_controller
            )
            self.platform_tabs.setup_ui()
            
    
    def run(self):
        """Start the GUI application."""
        dpg.create_context()
        dpg.create_viewport(title="MCAT Content Moderation Checker", width=1050, height=850)
        
        # Apply global theme
        AppTheme.apply_themes()
        
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
        # Status display was removed, this method is kept for compatibility
        # but does nothing. Status is now shown in individual tabs.
        pass
    
    
    
    
    # Removed _on_state_changed - state updates now handled by ProcessingCoordinator
    
    
    
    
    
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
    
    def _on_progress_update(self, current_stats: dict, total_count: int, processed_count: int, current_action: str = ""):
        """Handle progress updates from processing controller."""
        # Delegate to YouTube tab
        if self.platform_tabs and self.platform_tabs.get_youtube_tab():
            self.platform_tabs.get_youtube_tab()._on_progress_update(current_stats, total_count, processed_count, current_action)
    
    
    # Removed duplicate _on_state_changed method
