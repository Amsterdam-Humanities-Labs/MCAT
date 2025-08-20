import dearpygui.dearpygui as dpg
from typing import Optional, Dict
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from ..widgets.progress_bar_segmented import RectangularProgress


class DataPanel:
    """Reusable data panel component for displaying processing results and progress."""
    
    def __init__(self, parent_window: str, platform: str):
        self.parent_window = parent_window
        self.platform = platform
        
        # Components
        self.progress_bar: Optional[RectangularProgress] = None
        
        # UI element IDs
        self.panel_id = f"data_panel_{platform}"
        self.progress_group_id = f"progress_group_{platform}"
    
    def setup_ui(self) -> None:
        """Create the data panel UI components."""
        # Create right panel that takes remaining space (60% of screen width)
        with dpg.child_window(
            tag=self.panel_id,
            parent=self.parent_window,
            width=-1,  # Take remaining width
            height=-1,
            border=False,
            horizontal_scrollbar=False
        ):
            dpg.add_text(f"{self.platform.title()} Data", color=[255, 255, 255])
            dpg.add_spacer(height=20)
            
            # Progress section (temporarily visible for testing)
            with dpg.group(tag=self.progress_group_id, show=True):
                self.progress_bar = RectangularProgress(
                    parent_window=self.progress_group_id,
                    width=400,
                    height=50
                )
                self.progress_bar.setup_ui(label="Processing Progress")
                
                dpg.add_spacer(height=20)
            
            # Placeholder for future components (results table, export options, etc.)
            dpg.add_text("Results will appear here after processing", color=[120, 120, 120])
    
    def show_progress(self) -> None:
        """Show the progress section."""
        if dpg.does_item_exist(self.progress_group_id):
            dpg.configure_item(self.progress_group_id, show=True)
    
    def hide_progress(self) -> None:
        """Hide the progress section."""
        if dpg.does_item_exist(self.progress_group_id):
            dpg.configure_item(self.progress_group_id, show=False)
    
    def update_progress(self, status_counts: Dict[str, int]) -> None:
        """Update the progress bar with new status counts."""
        if self.progress_bar:
            self.progress_bar.update_progress(status_counts)
    
    def reset_progress(self) -> None:
        """Reset the progress bar to initial state."""
        if self.progress_bar:
            self.progress_bar.reset()
    
    def start_processing(self) -> None:
        """Called when processing starts."""
        self.show_progress()
        self.reset_progress()
    
    def finish_processing(self) -> None:
        """Called when processing finishes."""
        # Keep progress visible to show final results
        pass
    
    def get_progress_stats(self) -> Dict[str, int]:
        """Get current progress statistics."""
        if self.progress_bar:
            return self.progress_bar.get_status_counts()
        return {}