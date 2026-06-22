"""Thread-safe event bus for SSE broadcasting."""

import threading
from queue import Queue, Empty


class EventBus:
    """Publish-subscribe event bus. Subscribers receive events via queues."""

    def __init__(self):
        self._subscribers: set[Queue] = set()
        self._lock: threading.Lock = threading.Lock()

    def subscribe(self) -> Queue[dict]:
        queue: Queue[dict] = Queue()
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: Queue[dict]) -> None:
        with self._lock:
            self._subscribers.discard(queue)

    def publish(self, event: dict) -> None:
        with self._lock:
            dead_queues = []
            for queue in self._subscribers:
                try:
                    queue.put_nowait(event)
                except Exception:
                    dead_queues.append(queue)
            for q in dead_queues:
                self._subscribers.discard(q)

    def get_event(self, queue: Queue[dict], timeout: float | None = None) -> dict | None:
        try:
            return queue.get(timeout=timeout)
        except Empty:
            return None


event_bus = EventBus()
