"""
Service for managing scheduled URL tracking.

Tracks URLs periodically to detect status changes while app is running.
"""

import threading
from datetime import datetime, timedelta
from typing import Optional

import polars as pl

from models.project_state import ProjectState
from models.project_models import RunStatus


class TrackingService:
    """Manages scheduled tracking runs for URL status monitoring."""

    def __init__(self):
        self._timer: Optional[threading.Timer] = None
        self._stop_event = threading.Event()
        self._project_state: Optional[ProjectState] = None
        self._interval_minutes: int = 60
        self._processing_service = None
        self._run_service = None
        self._log_callback = None
        self._event_bus = None

    def initialize(self, processing_service, run_service, log_callback, event_bus):
        """Initialize tracking service with dependencies."""
        self._processing_service = processing_service
        self._run_service = run_service
        self._log_callback = log_callback
        self._event_bus = event_bus

    def start_tracking(self, project_state: ProjectState, interval_minutes: int) -> dict:
        """
        Start periodic tracking scheduler.

        Args:
            project_state: Current project state
            interval_minutes: Interval between checks in minutes

        Returns:
            Dict with next_check timestamp and status
        """
        self._project_state = project_state
        self._interval_minutes = interval_minutes
        self._stop_event.clear()

        # Update project configuration
        project_state.config.tracking.enabled = True
        project_state.config.tracking.interval_minutes = interval_minutes
        project_state.config.tracking.next_check = datetime.now() + timedelta(minutes=interval_minutes)
        project_state.save()

        # Log and publish event
        if self._log_callback:
            self._log_callback(
                f"URL tracking started (every {interval_minutes} minutes)",
                "info"
            )

        if self._event_bus:
            self._event_bus.publish({
                "type": "tracking.started",
                "interval_minutes": interval_minutes,
                "next_check": project_state.config.tracking.next_check.isoformat(),
            })

        # Schedule first check
        self._schedule_next_check()

        return {
            "enabled": True,
            "interval_minutes": interval_minutes,
            "next_check": project_state.config.tracking.next_check.isoformat(),
        }

    def stop_tracking(self, project_state: ProjectState) -> dict:
        """
        Cancel tracking scheduler.

        Args:
            project_state: Current project state

        Returns:
            Dict with stopped status
        """
        if self._timer:
            self._timer.cancel()
            self._timer = None

        self._stop_event.set()

        # Update project configuration
        project_state.config.tracking.enabled = False
        project_state.save()

        # Log and publish event
        if self._log_callback:
            self._log_callback("URL tracking stopped", "info")

        if self._event_bus:
            self._event_bus.publish({
                "type": "tracking.stopped",
            })

        return {"enabled": False}

    def get_tracking_status(self, project_state: ProjectState) -> dict:
        """
        Get current tracking status.

        Args:
            project_state: Current project state

        Returns:
            Dict with tracking status
        """
        config = project_state.config.tracking
        return {
            "enabled": config.enabled,
            "interval_minutes": config.interval_minutes,
            "last_check": config.last_check.isoformat() if config.last_check else None,
            "next_check": config.next_check.isoformat() if config.next_check else None,
        }

    def _schedule_next_check(self):
        """Schedule next check using threading.Timer."""
        if self._stop_event.is_set():
            return

        if self._timer:
            self._timer.cancel()

        interval_seconds = self._interval_minutes * 60
        self._timer = threading.Timer(interval_seconds, self._execute_tracking_run)
        self._timer.daemon = True
        self._timer.start()

    def _execute_tracking_run(self):
        """Execute a tracking run."""
        if not self._project_state or self._stop_event.is_set():
            return

        try:
            # Check if manual processing is active (skip if so)
            if self._project_state.is_running:
                if self._log_callback:
                    self._log_callback("Tracking skipped: manual processing in progress", "debug")
                # Reschedule for later
                self._schedule_next_check()
                return

            # Create tracking run
            if self._run_service:
                run = self._run_service.start_run(
                    self._project_state,
                    screenshots_enabled=False,
                    run_type="tracking"
                )

                if self._log_callback:
                    self._log_callback(f"Tracking check started: {run.id}", "info")

                # Publish event
                if self._event_bus:
                    self._event_bus.publish({
                        "type": "tracking.run_started",
                        "run_id": run.id,
                    })

                # Read URLs from urls.csv
                all_urls_df = pl.read_csv(self._project_state.urls_csv_path)
                urls = all_urls_df.select(
                    pl.col(self._project_state.url_column).drop_nulls().cast(pl.Utf8)
                ).to_series().to_list()

                # Start processing
                if self._processing_service:
                    from models.file_models import FileInfo, ColumnMapping
                    from models.processing_models import ProcessingJob

                    file_info = FileInfo(path=str(self._project_state.urls_csv_path))
                    file_info.dataframe = all_urls_df
                    file_info.row_count = len(all_urls_df)
                    file_info.columns = all_urls_df.columns
                    file_info.valid = True

                    column_mapping = ColumnMapping()
                    column_mapping.post_column = self._project_state.url_column

                    job = ProcessingJob(
                        file_info=file_info,
                        column_mapping=column_mapping,
                        platform=self._project_state.platform,
                        output_folder=str(self._project_state.get_run_path(run.id)),
                        save_screenshots=False
                    )

                    self._processing_service.start_processing(job, urls=urls)

        except Exception as e:
            if self._log_callback:
                self._log_callback(f"Tracking error: {str(e)}", "error")
        finally:
            # Schedule next check
            if not self._stop_event.is_set():
                self._schedule_next_check()
