import dearpygui.dearpygui as dpg
import pandas as pd
from typing import Optional
import sys
import os

# config import removed - not used in this file
# from utils.csv_handler import CSVHandler  # Not needed in MainWindow
from gui.components.containers.tab_container_platforms import PlatformTabs
# from gui.processing_controller import ProcessingController  # Removed - merged into ProcessingService
from services.processing_service import ProcessingService
from gui.theme import AppTheme


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for Nuitka."""
    if getattr(sys, 'frozen', False) or '/tmp/onefile_' in __file__:
        # Running in Nuitka onefile binary - assets are in temp directory
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller style
            base_path = sys._MEIPASS
        else:
            # Nuitka onefile - get the temp extraction directory
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resource_path = os.path.join(base_path, relative_path)
    else:
        # Running in development
        base_path = os.path.dirname(__file__)
        resource_path = os.path.join(base_path, "..", "..", relative_path)
    
    return os.path.abspath(resource_path)


class MainWindow:
    """Primary GUI controller using Dear PyGui."""
    
    def __init__(self):
        self.platform_tabs: Optional[PlatformTabs] = None
        
        # UI element IDs
        self.main_window_id = "main_window"
    
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
                font_path = get_resource_path("assets/fonts/NotoSans-Medium.ttf")
                
                if os.path.exists(font_path):
                    large_font = dpg.add_font(font_path, 22)
                else:
                    large_font = None
            
            if large_font:
                dpg.bind_font(large_font)
 
            # Platform Tabs
            self.platform_tabs = PlatformTabs(
                parent_window=self.main_window_id
            )
            self.platform_tabs.setup_ui()
            
    
    def run(self):
        """Start the GUI application with progress processing main loop."""
        dpg.create_context()
        dpg.configure_app(manual_callback_management=True)  # Enable manual callback management
        dpg.create_viewport(title="MCAT Content Moderation Checker", width=1050, height=850)
        
        # Apply global theme
        AppTheme.apply_themes()
        
        self.setup_ui()
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.main_window_id, True)
        
        try:
            # Main event loop with progress processing
            while dpg.is_dearpygui_running():
                # Process Dear PyGui callbacks
                jobs = dpg.get_callback_queue()
                dpg.run_callbacks(jobs)
                
                # Process progress updates from all ProcessingService instances
                ProcessingService.process_all_progress_updates()
                
                # Render frame
                dpg.render_dearpygui_frame()
        finally:
            # Cleanup components
            if self.platform_tabs:
                self.platform_tabs.cleanup()
            dpg.destroy_context()
    
    
    
    
    def _update_status(self, message: str, color: list = None):
        """Update the status display."""
        # Status display was removed, this method is kept for compatibility
        # but does nothing. Status is now shown in individual tabs.
        pass
    
    
    
    
    # Removed _on_state_changed - state updates now handled by ProcessingCoordinator
    
    
    
    
    
    # Removed callback methods - processing now handled via MVP pattern:
    # - _on_processing_complete: Events → Presenter → View
    # - _on_processing_error: Events → Presenter → View
    # - _on_progress_update: Events → Presenter → View
    # MainWindow no longer needs to handle processing events directly
    
    
    # Removed duplicate _on_state_changed method
