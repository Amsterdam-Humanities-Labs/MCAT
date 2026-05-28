from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass, field
import threading


@dataclass
class ScrapingResult:
    """Standardized result format for all scrapers."""

    url: str = ""
    status: str = ""
    info: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    error_message: str = ""
    screenshot_path: str = ""


class BaseScraper(ABC):
    """Abstract base class for all platform scrapers."""

    cancel_event: threading.Event | None = None
    pause_event: threading.Event | None = None

    @abstractmethod
    def check_url_status(self, url: str) -> ScrapingResult:
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        pass

    def set_cancel_event(self, cancel_event: threading.Event) -> None:
        self.cancel_event = cancel_event

    def set_pause_event(self, pause_event: threading.Event) -> None:
        self.pause_event = pause_event

    def is_cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()

    def enable_screenshots(self, enabled: bool, base_path: str) -> None:
        pass

    def cleanup(self) -> None:
        pass
