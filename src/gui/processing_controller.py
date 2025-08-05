import threading
from typing import Dict, Optional, Callable
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.batch_processor import BatchProcessor
from utils.state_manager import StateManager, ProcessingState
from utils.csv_handler import CSVHandler


class ProcessingController:
    """Controller that handles URL processing coordination between GUI and BatchProcessor."""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
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
    
    def set_callbacks(self, 
                     on_results_updated: Callable = None,
                     on_processing_complete: Callable = None, 
                     on_processing_error: Callable = None):
        """Set callback functions for processing events."""
        self.on_results_updated = on_results_updated
        self.on_processing_complete = on_processing_complete
        self.on_processing_error = on_processing_error
    
    def start_processing(self, df: pd.DataFrame, column_mapping: Dict[str, str], platform: str = "youtube"):
        """Start processing URLs in a separate thread."""
        if self.is_processing:
            raise RuntimeError("Processing is already in progress")
        
        self.current_df = df.copy()
        self.column_mapping = column_mapping
        self.platform = platform
        self.is_processing = True
        
        # Initialize batch processor
        self.batch_processor = BatchProcessor(self.state_manager)
        
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
                
                self.state_manager.broadcast_state(
                    ProcessingState.COMPLETED,
                    {'stats': result.stats, 'processed_count': result.processed_count}
                )
            else:
                # Handle processing error
                if self.on_processing_error:
                    self.on_processing_error(result.error_message)
                
                self.state_manager.broadcast_state(ProcessingState.ERROR)
            
            # Clean up temp file
            try:
                os.remove(temp_csv_path)
            except:
                pass
                
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            if self.on_processing_error:
                self.on_processing_error(error_msg)
            
            self.state_manager.broadcast_state(ProcessingState.ERROR)
        
        finally:
            self.is_processing = False
    
    def cancel_processing(self):
        """Cancel the current processing operation."""
        if self.batch_processor:
            self.batch_processor.cancel_processing()
        
        if self.processing_thread and self.processing_thread.is_alive():
            # Wait for thread to finish cleanup
            self.processing_thread.join(timeout=2.0)
        
        self.is_processing = False
        self.state_manager.broadcast_state(ProcessingState.CANCELLED)
    
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