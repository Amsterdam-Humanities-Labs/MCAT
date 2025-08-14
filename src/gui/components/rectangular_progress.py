import dearpygui.dearpygui as dpg
from typing import Dict, Optional, Tuple
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class RectangularProgress:
    """Reusable rectangular progress bar component showing URL processing distribution."""
    
    # Status colors (RGB tuples)
    STATUS_COLORS = {
        'pending': (80, 80, 80),      # Gray - not yet processed
        'live': (0, 180, 0),          # Green - content is live
        'removed': (220, 50, 50),     # Red - content removed/deleted
        'restricted': (255, 140, 0),  # Orange - age restricted/private
        'error': (150, 30, 30),       # Dark red - processing errors
        'skipped': (255, 200, 0)      # Yellow - skipped URLs
    }
    
    def __init__(self, parent_window: str, width: int = 300, height: int = 40):
        self.parent_window = parent_window
        self.width = width
        self.height = height
        
        # Status counts
        self.status_counts: Dict[str, int] = {
            'pending': 0,
            'live': 0,
            'removed': 0,
            'restricted': 0,
            'error': 0,
            'skipped': 0
        }
        
        # UI element IDs
        self.container_id = f"progress_container_{id(self)}"
        self.drawlist_id = f"progress_drawlist_{id(self)}"
        self.counter_text_id = f"progress_counter_{id(self)}"
        self.legend_group_id = f"progress_legend_{id(self)}"
        
        # Progress tracking
        self.total_count = 0
        self.processed_count = 0
    
    def setup_ui(self, label: str = "Processing Progress") -> None:
        """Create the progress bar UI components."""
        with dpg.group(tag=self.container_id, parent=self.parent_window):
            # Label
            if label:
                dpg.add_text(label, color=[255, 255, 255])
                dpg.add_spacer(height=5)
            
            # Drawing area
            with dpg.drawlist(
                tag=self.drawlist_id,
                width=self.width,
                height=self.height
            ):
                # Draw initial empty state (all gray)
                self._draw_segments()
            
            # Progress counter below the bar
            dpg.add_spacer(height=5)
            dpg.add_text("0 / 0", tag=self.counter_text_id, color=[180, 180, 180])
            
            # Legend below the counter
            dpg.add_spacer(height=10)
            self._create_legend()
    
    def update_progress(self, status_counts: Dict[str, int], total: int = 0, processed: int = 0) -> None:
        """Update the progress bar with new status counts."""
        # Update internal counts
        for status in self.status_counts.keys():
            self.status_counts[status] = status_counts.get(status, 0)
        
        # Update progress tracking
        if total > 0:
            self.total_count = total
        if processed > 0:
            self.processed_count = processed
        
        # Redraw the progress bar
        self._draw_segments()
        
        # Update counter text
        self._update_counter_text()
    
    def reset(self) -> None:
        """Reset the progress bar to initial empty state."""
        self.status_counts = {status: 0 for status in self.status_counts.keys()}
        self.total_count = 0
        self.processed_count = 0
        self._draw_segments()
        self._update_counter_text()
    
    def _draw_segments(self) -> None:
        """Draw the rectangular segments based on current status counts."""
        if not dpg.does_item_exist(self.drawlist_id):
            return
        
        # Clear previous drawings
        dpg.delete_item(self.drawlist_id, children_only=True)
        
        # Calculate total count
        total_count = sum(self.status_counts.values())
        
        # If no data, show all gray (pending state)
        if total_count == 0:
            dpg.draw_rectangle(
                pmin=(0, 0),
                pmax=(self.width, self.height),
                color=self.STATUS_COLORS['pending'],
                fill=self.STATUS_COLORS['pending'],
                parent=self.drawlist_id
            )
            return
        
        # Draw segments left to right
        current_x = 0
        
        # Define order for consistent left-to-right layout
        status_order = ['live', 'removed', 'restricted', 'error', 'skipped', 'pending']
        
        for status in status_order:
            count = self.status_counts[status]
            if count == 0:
                continue
            
            # Calculate segment width
            segment_width = (count / total_count) * self.width
            
            # Draw the segment
            dpg.draw_rectangle(
                pmin=(current_x, 0),
                pmax=(current_x + segment_width, self.height),
                color=self.STATUS_COLORS[status],
                fill=self.STATUS_COLORS[status],
                parent=self.drawlist_id
            )
            
            # Move to next position
            current_x += segment_width
        
        # Draw border around entire progress bar
        dpg.draw_rectangle(
            pmin=(0, 0),
            pmax=(self.width, self.height),
            color=(100, 100, 100),
            thickness=1,
            parent=self.drawlist_id
        )
    
    def get_status_counts(self) -> Dict[str, int]:
        """Get current status counts."""
        return self.status_counts.copy()
    
    def get_total_count(self) -> int:
        """Get total number of items processed."""
        return sum(self.status_counts.values())
    
    def get_status_percentage(self, status: str) -> float:
        """Get percentage for a specific status."""
        total = self.get_total_count()
        if total == 0:
            return 0.0
        return (self.status_counts.get(status, 0) / total) * 100.0
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the component (visual state)."""
        if dpg.does_item_exist(self.container_id):
            dpg.configure_item(self.container_id, show=enabled)
    
    def _update_counter_text(self) -> None:
        """Update the progress counter text."""
        if dpg.does_item_exist(self.counter_text_id):
            counter_text = f"{self.processed_count} / {self.total_count}"
            dpg.set_value(self.counter_text_id, counter_text)
    
    def _create_legend(self) -> None:
        """Create a color legend explaining what each color means."""
        with dpg.group(tag=self.legend_group_id, horizontal=True, parent=self.container_id):
            
            # Legend items with color squares and labels
            legend_items = [
                ('live', 'Live', self.STATUS_COLORS['live']),
                ('removed', 'Removed/Unavailable', self.STATUS_COLORS['removed']),
                ('restricted', 'Restricted', self.STATUS_COLORS['restricted']),
                ('error', 'Error', self.STATUS_COLORS['error']),
                ('pending', 'Pending', self.STATUS_COLORS['pending'])
            ]
            
            for i, (status, label, color) in enumerate(legend_items):
                if i > 0:
                    dpg.add_spacer(width=15)  # Space between legend items
                
                # Create a small colored square
                with dpg.drawlist(width=12, height=12):
                    dpg.draw_rectangle(
                        pmin=(0, 0),
                        pmax=(12, 12),
                        color=color,
                        fill=color
                    )
                
                # Add label next to the square
                dpg.add_text(label, color=[200, 200, 200])