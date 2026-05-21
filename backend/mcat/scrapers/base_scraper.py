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

    def __init__(self, driver_manager: object):
        self.driver_manager: object = driver_manager
        self.cancel_event: threading.Event | None = None

    @abstractmethod
    def check_url_status(self, url: str) -> ScrapingResult:
        """Check the status of a single URL."""
        pass

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name for this scraper."""
        pass

    def set_cancel_event(self, cancel_event: threading.Event) -> None:
        """Set threading event for cancellation control."""
        self.cancel_event = cancel_event

    def is_cancelled(self) -> bool:
        """Check if processing has been cancelled."""
        return self.cancel_event is not None and self.cancel_event.is_set()

    def batch_check(self, urls: list[str]) -> list[ScrapingResult]:
        """Check multiple URLs in batch."""
        results = []
        for url in urls:
            result = self.check_url_status(url)
            results.append(result)
        return results

    def cleanup(self) -> None:
        """Clean up any resources used by the scraper."""
        pass
