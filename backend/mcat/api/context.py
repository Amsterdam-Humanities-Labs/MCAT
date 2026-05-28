"""Application context and shared state."""

import threading
from collections import deque
from datetime import datetime
from queue import Queue, Empty

from services.project_service import ProjectService
from services.run_service import RunService
from services.processing_service import ProcessingService
from services.tracking_service import TrackingService
from models.project_state import ProjectState
from models.import_result import UrlImportResult

MAX_LOG_ENTRIES = 100


class EventBus:
    """Thread-safe event bus for SSE broadcasting."""

    def __init__(self):
        self._subscribers: set[Queue] = set()
        self._lock: threading.Lock = threading.Lock()

    def subscribe(self) -> Queue[dict]:
        """Subscribe to events. Returns a queue to receive events."""
        queue: Queue[dict] = Queue()
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: Queue[dict]) -> None:
        """Unsubscribe from events."""
        with self._lock:
            self._subscribers.discard(queue)

    def publish(self, event: dict) -> None:
        """Publish an event to all subscribers."""
        with self._lock:
            dead_queues = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event)
                except Exception:
                    dead_queues.append(queue)
            # Clean up dead queues
            for q in dead_queues:
                self._subscribers.discard(q)

    def get_event(self, queue: Queue[dict], timeout: float | None = None) -> dict | None:
        """Get an event from a subscription queue."""
        try:
            return queue.get(timeout=timeout)
        except Empty:
            return None


class LogBuffer:
    """Thread-safe log buffer for frontend consumption."""

    def __init__(self, max_size: int = MAX_LOG_ENTRIES):
        self._logs: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._next_id = 0

    def add(self, text: str, level: str = "info") -> None:
        with self._lock:
            log_entry = {
                "id": self._next_id,
                "text": text,
                "level": level,
                "timestamp": datetime.now().isoformat(),
            }
            self._logs.append(log_entry)
            self._next_id += 1

        # Publish log event via SSE
        event_bus.publish({
            "type": "log",
            "log": log_entry,
        })

    def debug(self, text: str) -> None:
        self.add(text, "debug")

    def info(self, text: str) -> None:
        self.add(text, "info")

    def warning(self, text: str) -> None:
        self.add(text, "warning")

    def error(self, text: str) -> None:
        self.add(text, "error")

    def success(self, text: str) -> None:
        self.add(text, "success")

    def clear(self) -> None:
        with self._lock:
            self._logs.clear()


class AppContext:
    """Application context holding services and state."""

    _instance: "AppContext | None" = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "AppContext":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.project_service: ProjectService = ProjectService()
        self.run_service: RunService = RunService(log_callback=log_buffer.add)
        self.processing_service: ProcessingService | None = None
        self.tracking_service: TrackingService = TrackingService()
        self.current_project: ProjectState | None = None
        self._pending_import: "UrlImportResult | None" = None
        self._initialized: bool = True

    def set_project(self, project: ProjectState) -> None:
        """Set current project and initialize processing service."""
        import os
        self.current_project = project
        if self.processing_service:
            self.processing_service.cleanup()

        scraper_factory = None
        if os.environ.get("MCAT_MOCK"):
            from tests.mock_scraper_factory import create_mock_scraper
            scraper_factory = create_mock_scraper

        self.processing_service = ProcessingService(
            platform=project.platform,
            log_callback=log_buffer.add,
            scraper_factory=scraper_factory,
        )
        # Initialize tracking service with dependencies
        self.tracking_service.initialize(
            processing_service=self.processing_service,
            run_service=self.run_service,
            log_callback=log_buffer.add,
            event_bus=event_bus
        )

    def close_project(self) -> None:
        """Close current project and cleanup."""
        if self.current_project and self.tracking_service:
            self.tracking_service.stop_tracking(self.current_project)
        if self.current_project and self.current_project.current_run:
            self.run_service.abandon_run(self.current_project, self.current_project.current_run)
        if self.processing_service:
            self.processing_service.cleanup()
        self.current_project = None
        self.processing_service = None
        self._pending_import = None


# Global instances
event_bus = EventBus()
log_buffer = LogBuffer()
app_context = AppContext()
