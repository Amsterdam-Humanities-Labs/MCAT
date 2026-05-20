"""
Data models for processing operations.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import polars as pl

from .file_models import FileInfo, ColumnMapping


class ProcessingState(Enum):
    """Processing state enumeration."""
    IDLE = "idle"
    VALIDATING = "validating"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """Configuration for a processing job."""

    file_info: FileInfo
    column_mapping: ColumnMapping
    platform: str = "youtube"
    output_folder: str = ""
    save_screenshots: bool = False
    cookies: list = field(default_factory=list)
    auth_user: str = "anonymous"

    @property
    def is_valid(self) -> bool:
        """Check if job configuration is valid."""
        return (
            self.file_info.valid and
            self.column_mapping.is_valid and
            bool(self.platform)
        )


@dataclass
class ProcessingStatus:
    """Current status of a processing operation."""

    state: ProcessingState = ProcessingState.IDLE
    total_count: int = 0
    processed_count: int = 0
    current_action: str = ""
    stats: Dict[str, int] = field(default_factory=lambda: {
        'live': 0,
        'removed': 0,
        'restricted': 0,
        'errors': 0
    })
    error_message: str = ""

    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage (0-100)."""
        if self.total_count == 0:
            return 0.0
        return (self.processed_count / self.total_count) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if processing is complete."""
        return self.state in [ProcessingState.COMPLETED, ProcessingState.ERROR, ProcessingState.CANCELLED]

    @property
    def is_running(self) -> bool:
        """Check if processing is currently running."""
        return self.state == ProcessingState.PROCESSING

    @property
    def is_paused(self) -> bool:
        """Check if processing is paused."""
        return self.state == ProcessingState.PAUSED


@dataclass
class ProcessingResult:
    """Result of a completed processing operation."""

    success: bool = False
    dataframe: Optional[pl.DataFrame] = None
    stats: Dict[str, int] = field(default_factory=dict)
    processed_count: int = 0
    error_message: str = ""

    @classmethod
    def from_batch_result(cls, batch_result):
        """Create ProcessingResult from BatchProcessor result."""
        return cls(
            success=batch_result.success,
            dataframe=batch_result.dataframe,
            stats=batch_result.stats,
            processed_count=batch_result.processed_count,
            error_message=batch_result.error_message
        )
