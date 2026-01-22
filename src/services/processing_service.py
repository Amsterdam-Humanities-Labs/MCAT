"""
Unified processing service with thread-safe GUI communication.

Combines business logic coordination with background processing,
replacing the separate ProcessingController layer.
"""

import threading
import logging
import os
from typing import Optional, Dict, Set
from queue import Queue, Empty, Full
import pandas as pd

from models.processing_models import ProcessingJob, ProcessingStatus, ProcessingState, ProcessingResult
from models.file_models import ValidationResult, ColumnMapping
from core.batch_processor import BatchProcessor
from utils.csv_handler import CSVHandler
from events import dispatcher, ProcessingEvents


class ProcessingService:
    """Unified service for coordinating URL processing operations with threading."""
    
    # Class-level progress tracking for main loop processing
    _all_instances: Set['ProcessingService'] = set()
    _instances_lock = threading.Lock()
    
    def __init__(self):
        # State management with proper synchronization
        self._state_lock = threading.RLock()
        self._processing_state = ProcessingState.IDLE
        
        # Current processing data
        self.current_job: Optional[ProcessingJob] = None
        self.current_status = ProcessingStatus()
        
        # Threading components (absorbed from ProcessingController)
        self._processing_thread: Optional[threading.Thread] = None
        self._batch_processor: Optional[BatchProcessor] = None
        
        # Thread synchronization
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Start unpaused
        
        # Progress tracking (thread-safe)
        self._progress_queue = Queue(maxsize=20)
        
        # Register this instance for main loop progress processing
        with ProcessingService._instances_lock:
            ProcessingService._all_instances.add(self)
    
    @classmethod
    def is_any_processing(cls) -> bool:
        """Check if any service instance is currently processing."""
        with cls._instances_lock:
            for service in cls._all_instances:
                if service._processing_state in [ProcessingState.PROCESSING, ProcessingState.PAUSED]:
                    return True
        return False

    @classmethod
    def process_all_progress_updates(cls):
        """Process progress updates from all service instances (main thread)."""
        with cls._instances_lock:
            for service in cls._all_instances.copy():
                service._process_progress_updates()
    
    def _process_progress_updates(self):
        """Process progress updates for this service (called from main thread)."""
        try:
            while not self._progress_queue.empty():
                progress_data = self._progress_queue.get_nowait()
                
                # Update internal status
                with self._state_lock:
                    self.current_status.stats = progress_data.get('stats', {})
                    self.current_status.total_count = progress_data.get('total', 0)
                    self.current_status.processed_count = progress_data.get('current', 0)
                    self.current_status.current_action = progress_data.get('action', '')
                
                # Emit progress event (safe - we're on main thread)
                dispatcher.send(ProcessingEvents.PROGRESS, sender=self, status=self.current_status)
                
        except Empty:
            pass
        except Exception as e:
            logging.error(f"Progress update error: {e}")
    
    def validate_processing_request(self, job: ProcessingJob) -> ValidationResult:
        """
        Validate that a processing job can be started.
        
        Args:
            job: Processing job configuration
            
        Returns:
            ValidationResult: Validation result with errors if any
        """
        result = ValidationResult()
        
        # Check if already processing (thread-safe)
        with self._state_lock:
            if self._processing_state != ProcessingState.IDLE:
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
        Start a processing job with proper threading.
        
        Args:
            job: Processing job to execute
            
        Returns:
            True if processing started successfully, False otherwise
        """
        # Check if any other platform is already processing
        if ProcessingService.is_any_processing():
            dispatcher.send(ProcessingEvents.ERROR, sender=self, error_message="Another platform is already processing. Please wait or cancel it first.")
            return False

        # Validate the job first
        validation = self.validate_processing_request(job)
        if not validation.valid:
            error_msg = f"Cannot start processing: {validation.error_summary}"
            dispatcher.send(ProcessingEvents.ERROR, sender=self, error_message=error_msg)
            return False

        with self._state_lock:
            if self._processing_state != ProcessingState.IDLE:
                dispatcher.send(ProcessingEvents.ERROR, sender=self, error_message="Processing already in progress")
                return False
        
        try:
            # Store current job
            self.current_job = job
            self.current_status = ProcessingStatus(state=ProcessingState.PROCESSING)
            self.current_status.total_count = len(job.file_info.dataframe)
            
            # Reset synchronization events
            self._cancel_event.clear()
            self._pause_event.set()
            
            # Start processing thread (non-daemon for proper cleanup)
            self._processing_thread = threading.Thread(
                target=self._processing_worker,
                args=(job,),
                name=f"ProcessingWorker-{job.platform}",
                daemon=False
            )
            
            # Update state and emit started event
            with self._state_lock:
                self._processing_state = ProcessingState.PROCESSING
            
            dispatcher.send(ProcessingEvents.STARTED, sender=self, job=job, status=self.current_status)
            
            self._processing_thread.start()
            return True
            
        except Exception as e:
            with self._state_lock:
                self._processing_state = ProcessingState.ERROR
            self.current_status.state = ProcessingState.ERROR
            self.current_status.error_message = str(e)
            
            error_msg = f"Failed to start processing: {str(e)}"
            dispatcher.send(ProcessingEvents.ERROR, sender=self, error_message=error_msg)
            
            return False
    
    def pause_processing(self) -> bool:
        """
        Pause the current processing operation.
        
        Returns:
            True if paused successfully, False otherwise
        """
        with self._state_lock:
            if self._processing_state != ProcessingState.PROCESSING:
                return False
        
        try:
            # Signal pause to worker thread
            self._pause_event.clear()
            
            with self._state_lock:
                self._processing_state = ProcessingState.PAUSED
            self.current_status.state = ProcessingState.PAUSED
            
            # Tell batch processor to pause if it exists
            if self._batch_processor:
                self._batch_processor.pause_processing()
            
            dispatcher.send(ProcessingEvents.PAUSED, sender=self, status=self.current_status)
            return True
        except Exception as e:
            logging.error(f"Failed to pause processing: {e}")
            return False
    
    def resume_processing(self) -> bool:
        """
        Resume the paused processing operation.
        
        Returns:
            True if resumed successfully, False otherwise
        """
        with self._state_lock:
            if self._processing_state != ProcessingState.PAUSED:
                return False
        
        try:
            # Signal resume to worker thread
            self._pause_event.set()
            
            with self._state_lock:
                self._processing_state = ProcessingState.PROCESSING
            self.current_status.state = ProcessingState.PROCESSING
            
            # Tell batch processor to resume if it exists
            if self._batch_processor:
                self._batch_processor.resume_processing()
            
            dispatcher.send(ProcessingEvents.RESUMED, sender=self, status=self.current_status)
            return True
        except Exception as e:
            logging.error(f"Failed to resume processing: {e}")
            return False
    
    def cancel_processing(self) -> bool:
        """
        Cancel the current processing operation.
        
        Returns:
            True if cancelled successfully, False otherwise
        """
        with self._state_lock:
            if self._processing_state not in [ProcessingState.PROCESSING, ProcessingState.PAUSED]:
                return False
        
        try:
            # Signal cancellation to worker thread
            self._cancel_event.set()
            self._pause_event.set()  # Unblock if paused
            
            # Tell batch processor to cancel if it exists
            if self._batch_processor:
                self._batch_processor.cancel_processing()
            
            with self._state_lock:
                self._processing_state = ProcessingState.CANCELLED
            self.current_status.state = ProcessingState.CANCELLED
            
            dispatcher.send(ProcessingEvents.CANCELLED, sender=self, status=self.current_status)
            
            return True
        except Exception as e:
            logging.error(f"Failed to cancel processing: {e}")
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
        with self._state_lock:
            return self._processing_state == ProcessingState.PROCESSING
    
    def is_paused(self) -> bool:
        """Check if processing is paused."""
        with self._state_lock:
            return self._processing_state == ProcessingState.PAUSED
    
    def is_idle(self) -> bool:
        """Check if service is idle."""
        with self._state_lock:
            return self._processing_state == ProcessingState.IDLE
    
    def get_results(self) -> Optional[pd.DataFrame]:
        """
        Get processing results if available.
        
        Returns:
            Results dataframe or None if not available
        """
        if self._batch_processor:
            return self._batch_processor.get_results()
        return None
    
    def export_results(self, output_path: str) -> bool:
        """
        Export processing results to a file.
        
        Args:
            output_path: Path to save results
            
        Returns:
            True if export successful, False otherwise
        """
        if not self._batch_processor:
            return False
        
        try:
            results_df = self._batch_processor.get_results()
            if results_df is not None:
                CSVHandler.save_csv(results_df, output_path)
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to export results: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources and threads."""
        # Signal cancellation to all threads
        self._cancel_event.set()
        self._pause_event.set()
        
        # Wait for processing thread to finish
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=10.0)
            if self._processing_thread.is_alive():
                logging.warning("Processing thread did not terminate within 10s")
        
        # Cleanup batch processor
        if self._batch_processor:
            self._batch_processor.cleanup()
        
        # Reset state
        with self._state_lock:
            self._processing_state = ProcessingState.IDLE
        
        self.current_job = None
        self.current_status = ProcessingStatus()
        
        # Unregister from class tracking
        with ProcessingService._instances_lock:
            ProcessingService._all_instances.discard(self)
    
    # Internal worker methods
    def _processing_worker(self, job: ProcessingJob):
        """Main processing worker thread."""
        try:
            # Initialize batch processor in worker thread
            self._batch_processor = BatchProcessor()
            
            # Set progress callback to queue-based system
            self._batch_processor.set_progress_callback(self._queue_progress_update)
            
            # Save current dataframe to temp file for processing
            temp_csv_path = "/tmp/mcat_processing_temp.csv"
            CSVHandler.save_csv(job.file_info.dataframe, temp_csv_path)
            
            # Process the CSV
            result = self._batch_processor.process_csv(
                csv_path=temp_csv_path,
                platform=job.platform,
                column_mapping={'post': job.column_mapping.post_column},
                output_folder=job.output_folder,
                save_screenshots=job.save_screenshots
            )
            
            # Check for cancellation
            if self._cancel_event.is_set():
                return
            
            # Handle completion
            with self._state_lock:
                if self._processing_state == ProcessingState.CANCELLED:
                    return
                self._processing_state = ProcessingState.COMPLETED
            
            self.current_status.state = ProcessingState.COMPLETED
            
            if result.success:
                # Create a ProcessingResult from the raw result
                processing_result = ProcessingResult.from_batch_result(result)
                dispatcher.send(ProcessingEvents.COMPLETED, sender=self, result=processing_result, status=self.current_status)
            else:
                dispatcher.send(ProcessingEvents.ERROR, sender=self, error_message=result.error_message or "Processing failed")
            
        except Exception as e:
            with self._state_lock:
                self._processing_state = ProcessingState.ERROR
            self.current_status.state = ProcessingState.ERROR
            self.current_status.error_message = str(e)

            dispatcher.send(ProcessingEvents.ERROR, sender=self, error_message=str(e))

        finally:
            # Reset state to IDLE so new processing can start
            with self._state_lock:
                if self._processing_state in [ProcessingState.COMPLETED, ProcessingState.ERROR, ProcessingState.CANCELLED]:
                    self._processing_state = ProcessingState.IDLE

            # Cleanup temp file
            try:
                if os.path.exists("/tmp/mcat_processing_temp.csv"):
                    os.remove("/tmp/mcat_processing_temp.csv")
            except Exception:
                pass
    
    def _queue_progress_update(self, current_stats: dict, total_count: int, processed_count: int, current_action: str = ""):
        """Queue progress update from background thread (thread-safe)."""
        progress_data = {
            'stats': current_stats.copy() if current_stats else {},
            'total': total_count,
            'current': processed_count,
            'action': current_action
        }
        
        try:
            # Non-blocking put with size limit
            if self._progress_queue.full():
                try:
                    self._progress_queue.get_nowait()  # Remove oldest
                except Empty:
                    pass
            
            self._progress_queue.put_nowait(progress_data)
        except Full:
            pass  # Skip this update if queue is full
        except Exception as e:
            logging.error(f"Failed to queue progress update: {e}")