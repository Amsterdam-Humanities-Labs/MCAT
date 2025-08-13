import dearpygui.dearpygui as dpg
from typing import Optional
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .youtube_tab import YouTubeTab


class PlatformTabs:
    """Platform-specific scraper tabs container."""
    
    def __init__(self, parent_window: str, state_manager, processing_controller):
        self.parent_window = parent_window
        self.state_manager = state_manager
        self.processing_controller = processing_controller
        
        # Tab components
        self.youtube_tab: Optional[YouTubeTab] = None
        
        # Tab bar ID
        self.tab_bar_id = "platform_tab_bar"
    
    def setup_ui(self):
        """Create the platform tabs UI."""
        with dpg.tab_bar(tag=self.tab_bar_id, parent=self.parent_window):
            
            # YouTube Tab
            with dpg.tab(label="YouTube"):
                self.youtube_tab = YouTubeTab(
                    parent_window=self.parent_window,
                    state_manager=self.state_manager,
                    processing_controller=self.processing_controller
                )
                self.youtube_tab.setup_ui()
            
            # Facebook Tab (placeholder)
            with dpg.tab(label="Facebook"):
                dpg.add_text("Facebook scraper - Coming soon", color=[150, 150, 150])
            
            # X/Twitter Tab (placeholder)
            with dpg.tab(label="X (Twitter)"):
                dpg.add_text("X/Twitter scraper - Coming soon", color=[150, 150, 150])
            
            # TikTok Tab (placeholder)
            with dpg.tab(label="TikTok"):
                dpg.add_text("TikTok scraper - Coming soon", color=[150, 150, 150])
    
    def get_youtube_tab(self) -> Optional[YouTubeTab]:
        """Get the YouTube tab component."""
        return self.youtube_tab
    
    def cleanup(self):
        """Clean up tab resources."""
        if self.youtube_tab:
            self.youtube_tab.cleanup()