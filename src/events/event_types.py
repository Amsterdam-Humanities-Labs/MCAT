"""
Event type constants for type safety with PyDispatcher.

Using constants instead of raw strings provides IDE autocomplete,
prevents typos, and makes refactoring easier.
"""


class ProcessingEvents:
    """Processing-related event types for service communication."""
    
    # Lifecycle events
    STARTED = "processing.started"
    COMPLETED = "processing.completed" 
    ERROR = "processing.error"
    CANCELLED = "processing.cancelled"
    
    # State change events
    PAUSED = "processing.paused"
    RESUMED = "processing.resumed"
    
    # Progress events
    PROGRESS = "processing.progress"


class FileEvents:
    """File-related event types for CSV operations."""
    
    LOADED = "file.loaded"
    LOAD_ERROR = "file.load_error"
    VALIDATED = "file.validated"
    VALIDATION_ERROR = "file.validation_error"
    COLUMN_MAPPING_CHANGED = "file.column_mapping_changed"


class ValidationEvents:
    """Validation-related event types."""
    
    VALIDATION_REQUESTED = "validation.requested"
    VALIDATION_PASSED = "validation.passed"
    VALIDATION_FAILED = "validation.failed"