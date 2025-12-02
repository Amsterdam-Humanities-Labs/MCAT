import dearpygui.dearpygui as dpg
from typing import Optional

from gui.components.containers.tab_container_platforms import PlatformTabs
from services.processing_service import ProcessingService
from gui.theme import AppTheme


# Removed get_resource_path - no longer needed for default font


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

            # Set default font size
            with dpg.font_registry():
                default_font = dpg.add_font("", 22)  # Default font at size 22
                dpg.bind_font(default_font)
 
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
    

