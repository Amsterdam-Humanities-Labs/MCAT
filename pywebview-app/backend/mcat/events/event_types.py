"""Event type constants for PyDispatcher."""


class ProcessingEvents:
    """Processing-related event types for service communication."""

    STARTED = "processing.started"
    COMPLETED = "processing.completed"
    ERROR = "processing.error"
    CANCELLED = "processing.cancelled"

    PAUSED = "processing.paused"
    RESUMED = "processing.resumed"

    PROGRESS = "processing.progress"
