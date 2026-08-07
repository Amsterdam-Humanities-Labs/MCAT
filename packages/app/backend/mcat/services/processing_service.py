"""
Processing service — coordinates batch processing with threading.
"""

import asyncio
import tempfile
import threading
import logging
import os
from collections.abc import Callable

from models.processing_models import ProcessingJob, ProcessingStatus, ProcessingState, ProcessingResult
from models.file_models import ValidationResult
from models.types import STATUS_BUCKETS
from core.batch_processor import BatchProcessor
from utils.csv_handler import save_csv, normalize_url
from events import event_bus
from services.processing_validator import validate_job
from services.progress_queue import ProgressQueue


class ProcessingService:

    def __init__(self, platform: str = "", log_callback: Callable | None = None, scraper_factory: Callable | None = None):
        self.platform: str = platform
        self._log_callback: Callable | None = log_callback
        self._scraper_factory: Callable | None = scraper_factory

        self._state_lock: threading.RLock = threading.RLock()
        self._processing_state: ProcessingState = ProcessingState.IDLE
        # Why the last start_processing was refused, for the API to relay to the UI.
        self.last_start_error: str = ""

        self.current_job: ProcessingJob | None = None
        self.current_status: ProcessingStatus = ProcessingStatus()
        self._custom_urls: list[str] | None = None

        self._processing_thread: threading.Thread | None = None
        self._batch_processor: BatchProcessor | None = None

        self._cancel_event: threading.Event = threading.Event()
        self._pause_event: threading.Event = threading.Event()
        self._pause_event.set()

        self._progress_queue: ProgressQueue = ProgressQueue()

        # Lifecycle callbacks — set by caller via start_processing
        self._on_completed: Callable | None = None
        self._on_error: Callable | None = None

    def set_log_callback(self, callback: Callable) -> None:
        self._log_callback = callback

    def validate_processing_request(self, job: ProcessingJob) -> ValidationResult:
        with self._state_lock:
            return validate_job(job, self._processing_state)

    def start_processing(
        self,
        job: ProcessingJob,
        urls: list[str] | None = None,
        on_completed: Callable | None = None,
        on_error: Callable | None = None,
    ) -> bool:
        # The lock is held from the idle check through the state change, so two
        # near-simultaneous starts cannot both pass and share one BatchProcessor.
        # _state_lock is reentrant, so the nested acquisitions below are fine.
        with self._state_lock:
            if not self.is_idle():
                self.last_start_error = "A run is already in progress"
                self._log_error(f"Cannot start: {self.last_start_error}")
                return False

            if urls is None:
                validation = self.validate_processing_request(job)
                if not validation.valid:
                    self.last_start_error = validation.error_summary
                    self._log_error(f"Cannot start: {self.last_start_error}")
                    return False

            self.last_start_error = ""
            try:
                self.current_job = job
                self._custom_urls = urls
                self._on_completed = on_completed
                self._on_error = on_error
                self.current_status = ProcessingStatus(state=ProcessingState.PROCESSING)
                self.current_status.total_count = len(urls) if urls else job.file_info.row_count

                self._cancel_event.clear()
                self._pause_event.set()

                # Build the batch processor on the calling thread, before the worker
                # starts, so a cancel/cleanup arriving during startup can reach it via
                # self._batch_processor instead of being dropped. Construction is cheap;
                # the driver pool is created lazily inside process_csv.
                self._batch_processor = BatchProcessor(scraper_factory=self._scraper_factory)
                self._batch_processor.set_progress_callback(self._queue_progress_update)
                if self._log_callback:
                    self._batch_processor.set_log_callback(self._log_callback)

                # Daemon so a wedged batch can never hold the interpreter open;
                # shutdown still joins it with a timeout for a clean teardown.
                self._processing_thread = threading.Thread(
                    target=self._processing_worker,
                    args=(job,),
                    name=f"ProcessingWorker-{job.platform}",
                    daemon=True
                )

                self._processing_state = ProcessingState.PROCESSING

                self._publish_status()
                self._processing_thread.start()
                return True

            except Exception as e:
                self.last_start_error = f"Failed to start: {e}"
                self._log_error(self.last_start_error)
                self._set_error_state(str(e))
                return False

    def pause_processing(self) -> bool:
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

            self._publish_status()
            return True
        except Exception as e:
            logging.error(f"Failed to pause processing: {e}")
            return False

    def resume_processing(self) -> bool:
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

            self._publish_status()
            return True
        except Exception as e:
            logging.error(f"Failed to resume processing: {e}")
            return False

    def cancel_processing(self) -> bool:
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

            self._publish_status()
            return True
        except Exception as e:
            logging.error(f"Failed to cancel processing: {e}")
            return False

    def get_current_status(self) -> ProcessingStatus:
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

    def join(self, timeout: float | None = None) -> bool:
        """Wait for the worker to finish. True if no worker is left running."""
        thread = self._processing_thread
        if thread is None or not thread.is_alive():
            return True
        thread.join(timeout)
        return not thread.is_alive()

    def cleanup(self) -> None:
        self._cancel_event.set()
        self._pause_event.set()

        # cancel_processing (not just the flags) is what stops the browser from
        # the worker's loop, so an in-flight page load unwinds now instead of
        # running out its 30s timeout.
        if self._batch_processor:
            self._batch_processor.cancel_processing()

        with self._state_lock:
            self._processing_state = ProcessingState.IDLE

        self.current_job = None
        self.current_status = ProcessingStatus()

    # Internal

    def _log_error(self, message: str) -> None:
        if self._log_callback:
            self._log_callback(message, "error")

    def _set_error_state(self, message: str) -> None:
        with self._state_lock:
            self._processing_state = ProcessingState.ERROR
        self.current_status.state = ProcessingState.ERROR
        self.current_status.error_message = message

    def _publish_status(self) -> None:
        """Publish current processing status via EventBus for SSE."""
        stats = self.current_status.stats or {}
        event_bus.publish({
            "type": "processing",
            "state": self.current_status.state.value if self.current_status.state else "idle",
            "total": self.current_status.total_count,
            "processed": self.current_status.processed_count,
            "status_counts": {k: stats.get(k, 0) for k in STATUS_BUCKETS},
            "action": self.current_status.current_action,
            "error": self.current_status.error_message,
        })

    def _queue_progress_update(self, stats: dict, total: int, processed: int, action: str = "") -> None:
        self._progress_queue.push(stats, total, processed, action)
        with self._state_lock:
            self.current_status.stats = stats
            self.current_status.total_count = total
            self.current_status.processed_count = processed
            self.current_status.current_action = action
        self._publish_status()

    def _processing_worker(self, job: ProcessingJob) -> None:
        _, temp_csv_path = tempfile.mkstemp(suffix='.csv', prefix='mcat_')

        try:
            processor = self._batch_processor
            if processor is None or self._cancel_event.is_set():
                return

            rows = job.file_info.rows or []
            if self._custom_urls:
                url_column = job.column_mapping.post_column
                # The selection holds normalized URLs, so the rows must be
                # normalized too or scheme-less and padded cells never match.
                custom_set = set(self._custom_urls)
                filtered = [r for r in rows if normalize_url(r.get(url_column, "")) in custom_set]
                if not filtered:
                    raise ValueError(
                        f"None of the {len(custom_set)} selected URLs matched a row "
                        f"in column '{url_column}'"
                    )
                save_csv(filtered, temp_csv_path)
            else:
                save_csv(rows, temp_csv_path)

            # Cancel/cleanup may have fired during startup or the save above; bail
            # before running the batch so we don't leave an orphan results.csv.
            if self._cancel_event.is_set():
                return

            # The async scraping batch runs in a fresh event loop owned by this
            # worker thread; the surrounding threading state machine, pause/cancel
            # events and SSE stay synchronous.
            result = asyncio.run(processor.process_csv_async(
                csv_path=temp_csv_path,
                platform=job.platform,
                column_mapping={'post': job.column_mapping.post_column},
                output_folder=job.output_folder,
                save_screenshots=job.save_screenshots,
                cookies=job.cookies,
                auth_user=job.auth_user,
            ))

            if self._cancel_event.is_set():
                return

            self._handle_completion(result)

        except Exception as e:
            if self._log_callback:
                self._log_callback(f"Processing error: {e}", "error")
            self._set_error_state(str(e))
            if self._on_error:
                self._on_error(str(e))
            self._publish_status()

        finally:
            with self._state_lock:
                if self._processing_state in [ProcessingState.COMPLETED, ProcessingState.ERROR, ProcessingState.CANCELLED]:
                    self._processing_state = ProcessingState.IDLE

            try:
                if os.path.exists(temp_csv_path):
                    os.remove(temp_csv_path)
            except Exception:
                pass

    def _handle_completion(self, result: ProcessingResult) -> None:
        with self._state_lock:
            if self._processing_state == ProcessingState.CANCELLED:
                return
            self._processing_state = ProcessingState.COMPLETED

        self.current_status.state = ProcessingState.COMPLETED

        if result.success:
            if self._log_callback:
                summary = ", ".join(f"{v} {k}" for k, v in result.stats.items() if v)
                self._log_callback(f"Completed: {summary or 'no results'}", "success")
            if self._on_completed:
                self._on_completed(result)
        else:
            if self._log_callback:
                self._log_callback(f"Processing failed: {result.error_message}", "error")
            if self._on_error:
                self._on_error(result.error_message or "Processing failed")

        self._publish_status()
