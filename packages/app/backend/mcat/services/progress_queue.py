"""Thread-safe progress queue for background processing."""

import logging
from collections.abc import Callable
from queue import Queue, Empty, Full


class ProgressQueue:
    """Thread-safe queue for progress updates from background threads."""

    def __init__(self, maxsize: int = 20):
        self._queue: Queue = Queue(maxsize=maxsize)

    def push(self, stats: dict, total: int, processed: int, action: str = "") -> bool:
        """
        Push a progress update (called from background thread).

        Args:
            stats: Current processing statistics
            total: Total items to process
            processed: Items processed so far
            action: Current action description

        Returns:
            True if pushed successfully
        """
        progress_data = {
            'stats': stats.copy() if stats else {},
            'total': total,
            'current': processed,
            'action': action
        }

        try:
            if self._queue.full():
                try:
                    self._queue.get_nowait()
                except Empty:
                    pass

            self._queue.put_nowait(progress_data)
            return True
        except Full:
            return False
        except Exception as e:
            logging.error(f"Failed to queue progress update: {e}")
            return False

    def pop(self) -> dict | None:
        """
        Pop a progress update (called from main thread).

        Returns:
            Progress data dict or None if empty
        """
        try:
            return self._queue.get_nowait()
        except Empty:
            return None

    def drain(self, callback: Callable[[dict], None]) -> None:
        """
        Drain all queued updates, calling callback for each.

        Args:
            callback: Function to call with each progress update
        """
        while True:
            data = self.pop()
            if data is None:
                break
            try:
                callback(data)
            except Exception as e:
                logging.error(f"Progress callback error: {e}")

    def clear(self) -> None:
        """Clear all queued updates."""
        while self.pop() is not None:
            pass

    @property
    def empty(self) -> bool:
        return self._queue.empty()
