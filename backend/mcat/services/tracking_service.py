"""
Service for managing scheduled URL tracking.
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from utils.csv_handler import get_urls_from_column

from models.project_state import ProjectState
from models.project_models import RunStatus

if TYPE_CHECKING:
    from api.context import EventBus
    from services.processing_service import ProcessingService
    from services.run_service import RunService


class TrackingService:
    """Manages scheduled tracking runs for URL status monitoring."""

    def __init__(self):
        self._timer: threading.Timer | None = None
        self._stop_event: threading.Event = threading.Event()
        self._project_state: ProjectState | None = None
        self._processing_service: ProcessingService | None = None
        self._run_service: RunService | None = None
        self._log_callback: Callable | None = None
        self._event_bus: EventBus | None = None

    def initialize(self, processing_service: ProcessingService, run_service: RunService, log_callback: Callable, event_bus: EventBus) -> None:
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
                from api.serializers import build_project_dict
                self._event_bus.publish({"type": "project", "project": build_project_dict()})
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

                if self._log_callback:
                    self._log_callback("Tracking started", "info")

                if self._processing_service:
                    from services.job_builder import build_processing_job

                    output_folder = str(self._project_state.get_run_path(run.id))
                    job = build_processing_job(self._project_state, output_folder, screenshots)

                    urls = get_urls_from_column(job.file_info.rows or [], self._project_state.url_column)
                    self._processing_service.start_processing(job, urls=urls)

        except Exception as e:
            if self._log_callback:
                self._log_callback(f"Tracking error: {str(e)}", "error")
        finally:
            # Schedule next check
            if not self._stop_event.is_set():
                self._schedule_next_check()
