from typing import Optional, Callable, Dict
import pandas as pd


class ProcessingCoordinator:
    """Coordinates processing workflow between UI components and processing controller."""
    
    def __init__(self, processing_controller):
        self.processing_controller = processing_controller
        
        # State
        self.is_processing = False
        self.is_paused = False
        
        # Current processing data
        self.current_df: Optional[pd.DataFrame] = None
        self.current_column_mapping: Dict[str, str] = {}
        self.current_platform: str = ""
        
        # UI callbacks
        self.on_progress_update: Optional[Callable] = None
        self.on_processing_complete: Optional[Callable] = None
        self.on_processing_error: Optional[Callable] = None
        self.on_ui_state_change: Optional[Callable] = None
        
        # Connect to processing controller
        if self.processing_controller:
            self.processing_controller.set_callbacks(
                on_processing_complete=self._handle_completion,
                on_processing_error=self._handle_error,
                on_progress_update=self._handle_progress
            )
    
    def set_callbacks(self,
                     on_progress_update: Callable = None,
                     on_processing_complete: Callable = None,
                     on_processing_error: Callable = None,
                     on_ui_state_change: Callable = None):
        """Set callback functions for processing events."""
        self.on_progress_update = on_progress_update
        self.on_processing_complete = on_processing_complete
        self.on_processing_error = on_processing_error
        self.on_ui_state_change = on_ui_state_change
    
    def start_processing(self, df: pd.DataFrame, column_mapping: Dict[str, str], platform: str = "youtube"):
        """Start processing with given parameters."""
        if self.is_processing:
            return False
        
        self.current_df = df
        self.current_column_mapping = column_mapping
        self.current_platform = platform
        self.is_processing = True
        self.is_paused = False
        
        # Update UI state
        self._notify_ui_state_change()
        
        # Start processing
        self.processing_controller.start_processing(df, column_mapping, platform)
        return True
    
    def pause_processing(self):
        """Pause the current processing."""
        if self.is_processing and not self.is_paused:
            self.is_paused = True
            self.processing_controller.pause_processing()
            self._notify_ui_state_change()
    
    def resume_processing(self):
        """Resume the paused processing."""
        if self.is_processing and self.is_paused:
            self.is_paused = False
            self.processing_controller.resume_processing()
            self._notify_ui_state_change()
    
    def cancel_processing(self):
        """Cancel the current processing."""
        if self.is_processing:
            self.processing_controller.cancel_processing()
            self._reset_state()
    
    def _handle_progress(self, current_stats: dict, total_count: int, processed_count: int):
        """Handle progress updates from processing controller."""
        if self.on_progress_update:
            self.on_progress_update(current_stats, total_count, processed_count)
    
    def _handle_completion(self, result):
        """Handle processing completion."""
        self._reset_state()
        if self.on_processing_complete:
            self.on_processing_complete(result)
    
    def _handle_error(self, error_message: str):
        """Handle processing error."""
        self._reset_state()
        if self.on_processing_error:
            self.on_processing_error(error_message)
    
    def _reset_state(self):
        """Reset processing state."""
        self.is_processing = False
        self.is_paused = False
        self._notify_ui_state_change()
    
    def _notify_ui_state_change(self):
        """Notify UI of state changes."""
        if self.on_ui_state_change:
            self.on_ui_state_change(self.is_processing, self.is_paused)
    
    def get_processing_state(self) -> tuple[bool, bool]:
        """Get current processing state (is_processing, is_paused)."""
        return self.is_processing, self.is_paused