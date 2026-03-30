"""
Unified processing service with thread-safe GUI communication.

Coordinates background processing with threading and progress reporting.
"""

import threading
import logging
import os
from typing import Optional, Set
import polars as pl

from models.processing_models import ProcessingJob, ProcessingStatus, ProcessingState, ProcessingResult
from models.file_models import ValidationResult
from core.batch_processor import BatchProcessor
from utils.csv_handler import CSVHandler
from events import dispatcher, ProcessingEvents
from services.processing_validator import validate_job
from services.progress_queue import ProgressQueue


class ProcessingService:
    """Unified service for coordinating URL processing operations with threading."""

    _all_instances: Set['ProcessingService'] = set()
    _instances_lock = threading.Lock()

    def __init__(self, platform: str = "", log_callback=None):
        self.platform = platform
        self._log_callback = log_callback

        # State management
        self._state_lock = threading.RLock()
        self._processing_state = ProcessingState.IDLE

        # Current processing data
        self.current_job: Optional[ProcessingJob] = None
        self.current_status = ProcessingStatus()
        self._custom_urls: Optional[list] = None

        # Threading components
        self._processing_thread: Optional[threading.Thread] = None
        self._batch_processor: Optional[BatchProcessor] = None

        # Thread synchronization
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()

        # Progress tracking
        self._progress_queue = ProgressQueue()

        with ProcessingService._instances_lock:
            ProcessingService._all_instances.add(self)

    def set_log_callback(self, callback):
        """Set the log callback for sending messages."""
        self._log_callback = callback

    # Class-level processing checks

    @classmethod
    def is_any_processing(cls) -> bool:
        """Check if any service instance is currently processing."""
        with cls._instances_lock:
            for service in cls._all_instances:
                if service._processing_state in [ProcessingState.PROCESSING, ProcessingState.PAUSED]:
                    return True
        return False

    # Public API

    def validate_processing_request(self, job: ProcessingJob) -> ValidationResult:
        """Validate that a processing job can be started."""
        with self._state_lock:
            return validate_job(job, self._processing_state)

    def start_processing(self, job: ProcessingJob, urls: list = None) -> bool:
        """Start a processing job with proper threading."""
        if ProcessingService.is_any_processing():
            dispatcher.send(ProcessingEvents.ERROR, sender=self,
                          error_message="Another platform is already processing. Please wait or cancel it first.")
            return False

        if urls is None:
            validation = self.validate_processing_request(job)
            if not validation.valid:
                dispatcher.send(ProcessingEvents.ERROR, sender=self,
                              error_message=f"Cannot start processing: {validation.error_summary}")
                return False

        with self._state_lock:
            if self._processing_state != ProcessingState.IDLE:
                dispatcher.send(ProcessingEvents.ERROR, sender=self,
                              error_message="Processing already in progress")
                return False

        try:
            self.current_job = job
            self._custom_urls = urls
            self.current_status = ProcessingStatus(state=ProcessingState.PROCESSING)
            self.current_status.total_count = len(urls) if urls else job.file_info.row_count

            self._cancel_event.clear()
            self._pause_event.set()

            self._processing_thread = threading.Thread(
                target=self._processing_worker,
                args=(job,),
                name=f"ProcessingWorker-{job.platform}",
                daemon=False
            )

            with self._state_lock:
                self._processing_state = ProcessingState.PROCESSING

            dispatcher.send(ProcessingEvents.STARTED, sender=self, job=job, status=self.current_status)
            self._processing_thread.start()
            return True

        except Exception as e:
            self._set_error_state(str(e))
            dispatcher.send(ProcessingEvents.ERROR, sender=self,
                          error_message=f"Failed to start processing: {e}")
            return False

    def pause_processing(self) -> bool:
        """Pause the current processing operation."""
        with self._state_lock:
            if self._processing_state != ProcessingState.PROCESSING:
                return False

        try:
            self._pause_event.clear()

            with self._state_lock:
                self._processing_state = ProcessingState.PAUSED
            self.current_status.state = ProcessingState.PAUSED

            if self._batch_processor:
                self._batch_processor.pause_processing()

            dispatcher.send(ProcessingEvents.PAUSED, sender=self, status=self.current_status)
            return True
        except Exception as e:
            logging.error(f"Failed to pause processing: {e}")
            return False

    def resume_processing(self) -> bool:
        """Resume the paused processing operation."""
        with self._state_lock:
            if self._processing_state != ProcessingState.PAUSED:
                return False

        try:
            self._pause_event.set()

            with self._state_lock:
                self._processing_state = ProcessingState.PROCESSING
            self.current_status.state = ProcessingState.PROCESSING

            if self._batch_processor:
                self._batch_processor.resume_processing()

            dispatcher.send(ProcessingEvents.RESUMED, sender=self, status=self.current_status)
            return True
        except Exception as e:
            logging.error(f"Failed to resume processing: {e}")
            return False

    def cancel_processing(self) -> bool:
        """Cancel the current processing operation."""
        with self._state_lock:
            if self._processing_state not in [ProcessingState.PROCESSING, ProcessingState.PAUSED]:
                return False

        try:
            self._cancel_event.set()
            self._pause_event.set()

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
        """Get the current processing status."""
        return self.current_status

    def is_processing(self) -> bool:
        with self._state_lock:
            return self._processing_state == ProcessingState.PROCESSING

    def is_paused(self) -> bool:
        with self._state_lock:
            return self._processing_state == ProcessingState.PAUSED

    def is_idle(self) -> bool:
        with self._state_lock:
            return self._processing_state == ProcessingState.IDLE

    def get_results(self) -> Optional[pl.DataFrame]:
        """Get processing results if available."""
        if self._batch_processor:
            return self._batch_processor.get_results()
        return None

    def export_results(self, output_path: str) -> bool:
        """Export processing results to a file."""
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
        self._cancel_event.set()
        self._pause_event.set()

        # Set batch processor cancel flag first so workers see it before drivers are killed
        if self._batch_processor:
            self._batch_processor.cancel_flag.set()
            self._batch_processor.resume_event.set()

        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=10.0)
            if self._processing_thread.is_alive():
                logging.warning("Processing thread did not terminate within 10s")

        if self._batch_processor:
            self._batch_processor.cleanup()

        with self._state_lock:
            self._processing_state = ProcessingState.IDLE

        self.current_job = None
        self.current_status = ProcessingStatus()

        with ProcessingService._instances_lock:
            ProcessingService._all_instances.discard(self)

    # Internal methods

    def _set_error_state(self, message: str):
        """Set error state with message."""
        with self._state_lock:
            self._processing_state = ProcessingState.ERROR
        self.current_status.state = ProcessingState.ERROR
        self.current_status.error_message = message

    def _process_progress_updates(self):
        """Process queued progress updates (called from main thread)."""
        def handle_update(data: dict):
            with self._state_lock:
                self.current_status.stats = data.get('stats', {})
                self.current_status.total_count = data.get('total', 0)
                self.current_status.processed_count = data.get('current', 0)
                self.current_status.current_action = data.get('action', '')
            dispatcher.send(ProcessingEvents.PROGRESS, sender=self, status=self.current_status)

        self._progress_queue.drain(handle_update)

    def _queue_progress_update(self, stats: dict, total: int, processed: int, action: str = ""):
        """Queue progress update from background thread and dispatch event."""
        self._progress_queue.push(stats, total, processed, action)
        # Update status and dispatch event immediately for SSE
        with self._state_lock:
            self.current_status.stats = stats
            self.current_status.total_count = total
            self.current_status.processed_count = processed
            self.current_status.current_action = action
        dispatcher.send(ProcessingEvents.PROGRESS, sender=self, status=self.current_status)

    def _processing_worker(self, job: ProcessingJob):
        """Main processing worker thread."""
        temp_csv_path = "/tmp/mcat_processing_temp.csv"

        try:
            self._batch_processor = BatchProcessor()
            self._batch_processor.set_progress_callback(self._queue_progress_update)
            if self._log_callback:
                self._batch_processor.set_log_callback(self._log_callback)

            if self._custom_urls:
                # Filter the original dataframe to only include custom URLs (preserves all columns)
                url_column = job.column_mapping.post_column
                temp_df = job.file_info.dataframe.filter(
                    pl.col(url_column).is_in(self._custom_urls)
                )
                temp_df.write_csv(temp_csv_path)
            else:
                CSVHandler.save_csv(job.file_info.dataframe, temp_csv_path)

            result = self._batch_processor.process_csv(
                csv_path=temp_csv_path,
                platform=job.platform,
                column_mapping={'post': job.column_mapping.post_column},
                output_folder=job.output_folder,
                save_screenshots=job.save_screenshots
            )

            if self._cancel_event.is_set():
                return

            self._handle_completion(result)

        except Exception as e:
            if self._log_callback:
                self._log_callback(f"Processing error: {e}", "error")
            self._set_error_state(str(e))
            dispatcher.send(ProcessingEvents.ERROR, sender=self, error_message=str(e))

        finally:
            with self._state_lock:
                if self._processing_state in [ProcessingState.COMPLETED, ProcessingState.ERROR, ProcessingState.CANCELLED]:
                    self._processing_state = ProcessingState.IDLE

            try:
                if os.path.exists(temp_csv_path):
                    os.remove(temp_csv_path)
            except Exception:
                pass

    def _handle_completion(self, result):
        """Handle processing completion."""
        with self._state_lock:
            if self._processing_state == ProcessingState.CANCELLED:
                return
            self._processing_state = ProcessingState.COMPLETED

        self.current_status.state = ProcessingState.COMPLETED

        if result.success:
            processing_result = ProcessingResult.from_batch_result(result)
            if self._log_callback:
                stats = result.stats
                self._log_callback(
                    f"Completed: {stats.get('live', 0)} live, {stats.get('removed', 0)} removed, "
                    f"{stats.get('restricted', 0)} restricted, {stats.get('errors', 0)} errors",
                    "success"
                )
            dispatcher.send(ProcessingEvents.COMPLETED, sender=self,
                          result=processing_result, status=self.current_status)
        else:
            if self._log_callback:
                self._log_callback(f"Processing failed: {result.error_message}", "error")
            dispatcher.send(ProcessingEvents.ERROR, sender=self,
                          error_message=result.error_message or "Processing failed")
