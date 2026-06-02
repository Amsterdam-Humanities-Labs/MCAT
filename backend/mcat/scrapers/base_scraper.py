import random
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


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

    # Rate limiting bounds in seconds (subclasses override).
    RATE_LIMIT_MIN: float = 1.0
    RATE_LIMIT_MAX: float = 3.0

    def __init__(self) -> None:
        self.min_delay: float = self.RATE_LIMIT_MIN
        self.max_delay: float = self.RATE_LIMIT_MAX
        self.last_request_time: float = 0.0
        self._rate_lock: threading.Lock = threading.Lock()

    def _apply_rate_limit(self) -> None:
        """Throttle requests across all worker threads sharing this scraper.

        A single scraper instance is shared by every worker, so the lock is held
        through the sleep: the shared timestamp acts as a true global spacer
        rather than letting workers read it together and fire in a burst.
        """
        with self._rate_lock:
            delay = random.uniform(self.min_delay, self.max_delay)
            wait = delay - (time.time() - self.last_request_time)
            if wait > 0:
                time.sleep(wait)
            self.last_request_time = time.time()

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
