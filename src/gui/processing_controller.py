import threading
import time
from typing import Dict, Optional, Callable
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.batch_processor import BatchProcessor
from utils.csv_handler import CSVHandler


class ProcessingController:
    """Controller that handles URL processing coordination between GUI and BatchProcessor."""
    
    def __init__(self):
        # Removed state_manager dependency
        self.batch_processor: Optional[BatchProcessor] = None
        self.processing_thread: Optional[threading.Thread] = None
        self.is_processing = False
        
        # Processing data
        self.current_df: Optional[pd.DataFrame] = None
        self.results_df: Optional[pd.DataFrame] = None
        self.column_mapping: Dict[str, str] = {}
        self.platform = "youtube"
        
        # Callbacks
        self.on_results_updated: Optional[Callable] = None
        self.on_processing_complete: Optional[Callable] = None
        self.on_processing_error: Optional[Callable] = None
        self.on_progress_update: Optional[Callable] = None
        
        # Progress monitoring
        self.progress_monitor_thread: Optional[threading.Thread] = None
        self.monitor_progress = False
    
    def set_callbacks(self, 
                     on_results_updated: Callable = None,
                     on_processing_complete: Callable = None, 
                     on_processing_error: Callable = None,
                     on_progress_update: Callable = None):
        """Set callback functions for processing events."""
        self.on_results_updated = on_results_updated
        self.on_processing_complete = on_processing_complete
        self.on_processing_error = on_processing_error
        self.on_progress_update = on_progress_update
    
    def start_processing(self, df: pd.DataFrame, column_mapping: Dict[str, str], platform: str = "youtube"):
        """Start processing URLs in a separate thread."""
        if self.is_processing:
            raise RuntimeError("Processing is already in progress")
        
        self.current_df = df.copy()
        self.column_mapping = column_mapping
        self.platform = platform
        self.is_processing = True
        
        # Initialize batch processor
        self.batch_processor = BatchProcessor()
        
        # Start progress monitoring
        self.monitor_progress = True
        self.progress_monitor_thread = threading.Thread(
            target=self._monitor_progress_thread,
            daemon=True
        )
        self.progress_monitor_thread.start()
        
        # Start processing in background thread
        self.processing_thread = threading.Thread(
            target=self._process_urls_thread,
            daemon=True
        )
        self.processing_thread.start()
    
    def _process_urls_thread(self):
        """Background thread for URL processing."""
        try:
            # Save current CSV to temp file for processing
            temp_csv_path = "/tmp/mcat_processing_temp.csv"
            CSVHandler.save_csv(self.current_df, temp_csv_path)
            
            # Process the CSV
            result = self.batch_processor.process_csv(
                csv_path=temp_csv_path,
                platform=self.platform,
                column_mapping=self.column_mapping
            )
            
            if result.success:
                self.results_df = result.dataframe
                
                # Notify completion
                if self.on_processing_complete:
                    self.on_processing_complete(result)
            else:
                # Handle processing error
                if self.on_processing_error:
                    self.on_processing_error(result.error_message)
            
            # Clean up temp file
            try:
                os.remove(temp_csv_path)
            except:
                pass
                
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            if self.on_processing_error:
                self.on_processing_error(error_msg)
        
        finally:
            self.is_processing = False
            self.monitor_progress = False
    
    def _monitor_progress_thread(self):
        """Monitor progress updates from batch processor and forward to GUI."""
        while self.monitor_progress and self.batch_processor:
            try:
                # Get progress updates from batch processor queue
                updates = self.batch_processor.get_progress_updates()
                
                # Forward most recent update to GUI callback
                if updates and self.on_progress_update:
                    latest_update = updates[-1]  # Get most recent
                    self.on_progress_update(
                        latest_update['stats'],
                        latest_update['total'], 
                        latest_update['current'],
                        latest_update.get('current_action', '')
                    )
                
                # Check every 100ms for smooth updates
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in progress monitor: {e}")
                time.sleep(0.5)
    
    def cancel_processing(self):
        """Cancel the current processing operation."""
        # Stop progress monitoring
        self.monitor_progress = False
        
        if self.batch_processor:
            self.batch_processor.cancel_processing()
        
        if self.processing_thread and self.processing_thread.is_alive():
            # Wait for thread to finish cleanup
            self.processing_thread.join(timeout=2.0)
        
        if self.progress_monitor_thread and self.progress_monitor_thread.is_alive():
            self.progress_monitor_thread.join(timeout=1.0)
        
        self.is_processing = False
        # State updates now handled by ProcessingCoordinator
    
    def pause_processing(self):
        """Pause the current processing operation."""
        if self.batch_processor and self.is_processing:
            self.batch_processor.pause_processing()
    
    def resume_processing(self):
        """Resume the paused processing operation."""
        if self.batch_processor and self.is_processing:
            self.batch_processor.resume_processing()
    
    def get_results(self) -> Optional[pd.DataFrame]:
        """Get the current processing results."""
        return self.results_df
    
    def export_results(self, output_path: str) -> bool:
        """Export results to a CSV file."""
        if self.results_df is None:
            raise ValueError("No results to export")
        
        try:
            CSVHandler.save_csv(self.results_df, output_path)
            return True
        except Exception as e:
            raise Exception(f"Failed to export results: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        if self.is_processing:
            self.cancel_processing()
        
        if self.batch_processor:
            self.batch_processor.cleanup()