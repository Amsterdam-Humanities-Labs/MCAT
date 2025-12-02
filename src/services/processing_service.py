"""
Processing coordination service.

Business logic for URL processing coordination without UI dependencies.
"""

import threading
from typing import Optional, Callable, Dict
import pandas as pd

from models.processing_models import ProcessingJob, ProcessingStatus, ProcessingState, ProcessingResult
from models.file_models import ValidationResult, ColumnMapping
from gui.processing_controller import ProcessingController


class ProcessingService:
    """Service for coordinating URL processing operations."""
    
    def __init__(self):
        self.processing_controller: Optional[ProcessingController] = None
        self.current_job: Optional[ProcessingJob] = None
        self.current_status = ProcessingStatus()
        
        # Callbacks for status updates
        self._on_progress_update: Optional[Callable] = None
        self._on_completion: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
    
    def set_callbacks(self, 
                     on_progress_update: Callable = None,
                     on_completion: Callable = None,
                     on_error: Callable = None):
        """
        Set callback functions for processing events.
        
        Args:
            on_progress_update: Called with (status) on progress updates
            on_completion: Called with (result) when processing completes
            on_error: Called with (error_message) on errors
        """
        self._on_progress_update = on_progress_update
        self._on_completion = on_completion
        self._on_error = on_error
    
    def validate_processing_request(self, job: ProcessingJob) -> ValidationResult:
        """
        Validate that a processing job can be started.
        
        Args:
            job: Processing job configuration
            
        Returns:
            ValidationResult: Validation result with errors if any
        """
        result = ValidationResult()
        
        # Check if already processing
        if self.is_processing():
            result.add_error("Processing is already in progress")
            return result
        
        # Validate job configuration
        if not job.is_valid:
            result.add_error("Invalid job configuration")
        
        if not job.file_info.valid:
            result.add_error("File is not valid")
        
        if not job.column_mapping.is_valid:
            result.add_error("Column mapping is not valid")
        
        if not job.platform:
            result.add_error("Platform must be specified")
        
        # Check that post column exists and has data
        if job.file_info.dataframe is not None:
            post_column = job.column_mapping.post_column
            if post_column in job.file_info.dataframe.columns:
                # Check for empty or null values in post column
                non_empty_count = job.file_info.dataframe[post_column].dropna().count()
                if non_empty_count == 0:
                    result.add_error(f"Post column '{post_column}' contains no valid URLs")
                elif non_empty_count < len(job.file_info.dataframe):
                    # This is a warning, not an error
                    pass
        
        # If no errors, mark as valid
        if not result.errors:
            result.valid = True
        
        return result
    
    def start_processing(self, job: ProcessingJob) -> bool:
        """
        Start a processing job.
        
        Args:
            job: Processing job to execute
            
        Returns:
            True if processing started successfully, False otherwise
        """
        # Validate the job first
        validation = self.validate_processing_request(job)
        if not validation.valid:
            if self._on_error:
                self._on_error(f"Cannot start processing: {validation.error_summary}")
            return False
        
        try:
            # Store current job
            self.current_job = job
            self.current_status = ProcessingStatus(state=ProcessingState.PROCESSING)
            
            # Initialize processing controller
            self.processing_controller = ProcessingController()
            self.processing_controller.set_callbacks(
                on_processing_complete=self._handle_completion,
                on_processing_error=self._handle_error,
                on_progress_update=self._handle_progress_update
            )
            
            # Prepare column mapping for processing controller
            column_mapping_dict = {
                'post': job.column_mapping.post_column
            }
            
            # Start processing
            self.processing_controller.start_processing(
                df=job.file_info.dataframe,
                column_mapping=column_mapping_dict,
                platform=job.platform
            )
            
            # Update status
            self.current_status.state = ProcessingState.PROCESSING
            self.current_status.total_count = len(job.file_info.dataframe)
            
            return True
            
        except Exception as e:
            self.current_status.state = ProcessingState.ERROR
            self.current_status.error_message = str(e)
            
            if self._on_error:
                self._on_error(f"Failed to start processing: {str(e)}")
            
            return False
    
    def pause_processing(self) -> bool:
        """
        Pause the current processing operation.
        
        Returns:
            True if paused successfully, False otherwise
        """
        if not self.is_processing():
            return False
        
        try:
            if self.processing_controller:
                self.processing_controller.pause_processing()
                self.current_status.state = ProcessingState.PAUSED
            return True
        except Exception:
            return False
    
    def resume_processing(self) -> bool:
        """
        Resume the paused processing operation.
        
        Returns:
            True if resumed successfully, False otherwise
        """
        if not self.is_paused():
            return False
        
        try:
            if self.processing_controller:
                self.processing_controller.resume_processing()
                self.current_status.state = ProcessingState.PROCESSING
            return True
        except Exception:
            return False
    
    def cancel_processing(self) -> bool:
        """
        Cancel the current processing operation.
        
        Returns:
            True if cancelled successfully, False otherwise
        """
        if not self.is_processing() and not self.is_paused():
            return False
        
        try:
            if self.processing_controller:
                self.processing_controller.cancel_processing()
            
            self.current_status.state = ProcessingState.CANCELLED
            self.current_job = None
            
            return True
        except Exception:
            return False
    
    def get_current_status(self) -> ProcessingStatus:
        """
        Get the current processing status.
        
        Returns:
            Current processing status
        """
        return self.current_status
    
    def is_processing(self) -> bool:
        """Check if currently processing."""
        return self.current_status.state == ProcessingState.PROCESSING
    
    def is_paused(self) -> bool:
        """Check if processing is paused."""
        return self.current_status.state == ProcessingState.PAUSED
    
    def is_idle(self) -> bool:
        """Check if service is idle."""
        return self.current_status.state == ProcessingState.IDLE
    
    def get_results(self) -> Optional[pd.DataFrame]:
        """
        Get processing results if available.
        
        Returns:
            Results dataframe or None if not available
        """
        if self.processing_controller:
            return self.processing_controller.get_results()
        return None
    
    def export_results(self, output_path: str) -> bool:
        """
        Export processing results to a file.
        
        Args:
            output_path: Path to save results
            
        Returns:
            True if export successful, False otherwise
        """
        if not self.processing_controller:
            return False
        
        try:
            return self.processing_controller.export_results(output_path)
        except Exception:
            return False
    
    def cleanup(self):
        """Clean up resources."""
        if self.processing_controller:
            self.processing_controller.cleanup()
        
        self.current_job = None
        self.current_status = ProcessingStatus()
    
    # Internal callback handlers
    def _handle_progress_update(self, current_stats: dict, total_count: int, processed_count: int, current_action: str = ""):
        """Handle progress updates from processing controller."""
        self.current_status.stats = current_stats
        self.current_status.total_count = total_count
        self.current_status.processed_count = processed_count
        self.current_status.current_action = current_action
        
        if self._on_progress_update:
            self._on_progress_update(self.current_status)
    
    def _handle_completion(self, result):
        """Handle processing completion."""
        self.current_status.state = ProcessingState.COMPLETED
        
        # Create a ProcessingResult from the raw result
        processing_result = ProcessingResult.from_batch_result(result)
        
        if self._on_completion:
            self._on_completion(processing_result)
    
    def _handle_error(self, error_message: str):
        """Handle processing error."""
        self.current_status.state = ProcessingState.ERROR
        self.current_status.error_message = error_message
        
        if self._on_error:
            self._on_error(error_message)