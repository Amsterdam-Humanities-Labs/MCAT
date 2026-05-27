"""
Service for managing scheduled URL tracking.

Tracks URLs periodically to detect status changes while app is running.
"""

import threading
from collections.abc import Callable
from datetime import datetime, timedelta

from utils.csv_handler import load_csv, get_columns, get_urls_from_column

from models.project_state import ProjectState
from models.project_models import RunStatus


class TrackingService:
    """Manages scheduled tracking runs for URL status monitoring."""

    def __init__(self):
        self._timer: threading.Timer | None = None
        self._stop_event: threading.Event = threading.Event()
        self._project_state: ProjectState | None = None
        self._processing_service: object | None = None
        self._run_service: object | None = None
        self._log_callback: Callable | None = None
        self._event_bus: object | None = None

    def initialize(self, processing_service: object, run_service: object, log_callback: Callable, event_bus: object) -> None:
        """Initialize tracking service with dependencies."""
        self._processing_service = processing_service
        self._run_service = run_service
        self._log_callback = log_callback
        self._event_bus = event_bus

    def start_tracking(self, project_state: ProjectState, interval_value: int, interval_unit: str = "minutes") -> dict:
        """
        Start periodic tracking scheduler.

        Args:
            project_state: Current project state
            interval_value: Interval value
            interval_unit: Interval unit ("minutes", "hours", "days")

        Returns:
            Dict with next_check timestamp and status
        """
        self._project_state = project_state
        self._stop_event.clear()

        # Update project configuration
        tracking = project_state.config.tracking
        tracking.enabled = True
        tracking.interval_value = interval_value
        tracking.interval_unit = interval_unit
        interval_seconds = tracking.interval_seconds
        tracking.next_check = datetime.now() + timedelta(seconds=interval_seconds)
        project_state.save()

        # Log and publish event
        if self._log_callback:
            self._log_callback(
                f"Tracking started (every {interval_value} {interval_unit})",
                "info"
            )

        # Schedule first check
        self._schedule_next_check()

        return {
            "enabled": True,
            "interval_value": interval_value,
            "interval_unit": interval_unit,
            "next_check": tracking.next_check.isoformat(),
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

        project_state.config.tracking.enabled = False
        project_state.save()

        if self._log_callback:
            self._log_callback("Tracking stopped", "info")

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
            "interval_value": config.interval_value,
            "interval_unit": config.interval_unit,
            "last_check": config.last_check.isoformat() if config.last_check else None,
            "next_check": config.next_check.isoformat() if config.next_check else None,
        }

    def _schedule_next_check(self) -> None:
        """Schedule next check using threading.Timer."""
        if self._stop_event.is_set():
            return

        if self._timer:
            self._timer.cancel()

        if self._project_state:
            interval_secs = self._project_state.config.tracking.interval_seconds
            # Update next_check so the frontend can show the countdown
            self._project_state.config.tracking.next_check = datetime.now() + timedelta(seconds=interval_secs)
            self._project_state.save()
            if self._event_bus:
                from api.handlers.project import _build_project_dict
                self._event_bus.publish({"type": "project", "project": _build_project_dict()})
        else:
            interval_secs = 1800  # fallback 30 min
        self._timer = threading.Timer(interval_secs, self._execute_tracking_run)
        self._timer.daemon = True
        self._timer.start()

    def _execute_tracking_run(self) -> None:
        """Execute a tracking run."""
        if not self._project_state or self._stop_event.is_set():
            return

        try:
            # Skip if a run is already active, wait and retry
            if self._project_state.is_running:
                self._timer = threading.Timer(5, self._execute_tracking_run)
                self._timer.daemon = True
                self._timer.start()
                return

            # Create tracking run
            if self._run_service:
                screenshots = self._project_state.config.screenshots_enabled
                run = self._run_service.start_run(
                    self._project_state,
                    screenshots_enabled=screenshots,
                    run_type="tracking"
                )

                # Tell mock scraper which run number this is
                import os
                if os.environ.get("MCAT_MOCK"):
                    os.environ["MCAT_MOCK_RUN"] = str(len(self._project_state.config.runs))

                if self._log_callback:
                    self._log_callback("Tracking started", "info")

                # Read URLs from urls.csv
                all_rows = load_csv(str(self._project_state.urls_csv_path))
                urls = get_urls_from_column(all_rows, self._project_state.url_column)

                # Start processing
                if self._processing_service:
                    from models.file_models import FileInfo, ColumnMapping
                    from models.processing_models import ProcessingJob

                    file_info = FileInfo(path=str(self._project_state.urls_csv_path))
                    file_info.rows = all_rows
                    file_info.row_count = len(all_rows)
                    file_info.columns = get_columns(all_rows)
                    file_info.valid = True

                    column_mapping = ColumnMapping()
                    column_mapping.post_column = self._project_state.url_column

                    job = ProcessingJob(
                        file_info=file_info,
                        column_mapping=column_mapping,
                        platform=self._project_state.platform,
                        output_folder=str(self._project_state.get_run_path(run.id)),
                        save_screenshots=screenshots
                    )

                    self._processing_service.start_processing(job, urls=urls)

        except Exception as e:
            if self._log_callback:
                self._log_callback(f"Tracking error: {str(e)}", "error")
        finally:
            # Schedule next check
            if not self._stop_event.is_set():
                self._schedule_next_check()
