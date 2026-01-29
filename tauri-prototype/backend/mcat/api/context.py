"""Application context and shared state."""

import threading
from collections import deque
from datetime import datetime
from typing import Optional

from services.project_service import ProjectService
from services.run_service import RunService
from services.processing_service import ProcessingService
from models.project_state import ProjectState

MAX_LOG_ENTRIES = 100


class LogBuffer:
    """Thread-safe log buffer for frontend consumption."""

    def __init__(self, max_size: int = MAX_LOG_ENTRIES):
        self._logs: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._next_id = 0

    def add(self, text: str, level: str = "info"):
        with self._lock:
            self._logs.append({
                "id": self._next_id,
                "text": text,
                "level": level,
                "timestamp": datetime.now().isoformat(),
            })
            self._next_id += 1

    def debug(self, text: str):
        self.add(text, "debug")

    def info(self, text: str):
        self.add(text, "info")

    def warning(self, text: str):
        self.add(text, "warning")

    def error(self, text: str):
        self.add(text, "error")

    def success(self, text: str):
        self.add(text, "success")

    def get_logs_since(self, since_id: int = -1) -> list:
        with self._lock:
            return [log for log in self._logs if log["id"] > since_id]

    def get_all(self) -> list:
        with self._lock:
            return list(self._logs)

    def clear(self):
        with self._lock:
            self._logs.clear()


class AppContext:
    """Application context holding services and state."""

    _instance: Optional["AppContext"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.project_service = ProjectService()
        self.run_service = RunService()
        self.processing_service: Optional[ProcessingService] = None
        self.current_project: Optional[ProjectState] = None
        self._pending_import = None
        self._initialized = True

    def set_project(self, project: ProjectState):
        """Set current project and initialize processing service."""
        self.current_project = project
        if self.processing_service:
            self.processing_service.cleanup()
        self.processing_service = ProcessingService(
            platform=project.platform,
            log_callback=lambda msg, level: log_buffer.add(msg, level)
        )

    def close_project(self):
        """Close current project and cleanup."""
        if self.processing_service:
            self.processing_service.cleanup()
        self.current_project = None
        self.processing_service = None
        self._pending_import = None


# Global instances
log_buffer = LogBuffer()
app_context = AppContext()
