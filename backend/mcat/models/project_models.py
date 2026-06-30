"""
Data models for project management.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import json

from .types import StatusSummary, empty_status_summary


class RunStatus(Enum):
    """Status of a processing run."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class RunConfig:
    """Configuration and state of a single processing run."""

    id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: RunStatus = RunStatus.IN_PROGRESS
    screenshots_enabled: bool = False
    run_type: str = "manual"  # "manual" or "tracking"
    is_baseline: bool = False
    duration_seconds: float = 0.0
    total_checked: int = 0
    changes_count: int = 0
    changes_summary: dict = field(default_factory=dict)
    status_summary: StatusSummary = field(default_factory=empty_status_summary)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "screenshots_enabled": self.screenshots_enabled,
            "run_type": self.run_type,
            "is_baseline": self.is_baseline,
            "duration_seconds": self.duration_seconds,
            "total_checked": self.total_checked,
            "changes_count": self.changes_count,
            "changes_summary": self.changes_summary,
            "status_summary": self.status_summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RunConfig":
        """Create RunConfig from dictionary."""
        return cls(
            id=data["id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            status=RunStatus(data["status"]),
            screenshots_enabled=data.get("screenshots_enabled", False),
            run_type=data.get("run_type", "manual"),
            is_baseline=data.get("is_baseline", False),
            duration_seconds=data.get("duration_seconds", 0.0),
            total_checked=data.get("total_checked", 0),
            changes_count=data.get("changes_count", 0),
            changes_summary=data.get("changes_summary", {}),
            status_summary=data.get("status_summary") or empty_status_summary(),
        )

    @property
    def is_complete(self) -> bool:
        """Check if run is complete."""
        return self.status == RunStatus.COMPLETED

    @property
    def is_interrupted(self) -> bool:
        """Check if run was interrupted (still in progress but not running)."""
        return self.status == RunStatus.IN_PROGRESS

    @property
    def is_tracking_run(self) -> bool:
        """Check if this is a tracking run."""
        return self.run_type == "tracking"


@dataclass
class TrackingConfig:
    """Configuration for URL tracking."""
    enabled: bool = False
    interval_value: int = 30
    interval_unit: str = "minutes"  # "minutes", "hours", "days"
    last_check: datetime | None = None
    next_check: datetime | None = None

    @property
    def interval_seconds(self) -> int:
        """Get interval in seconds."""
        multipliers = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}
        return self.interval_value * multipliers.get(self.interval_unit, 60)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "interval_value": self.interval_value,
            "interval_unit": self.interval_unit,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "next_check": self.next_check.isoformat() if self.next_check else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrackingConfig":
        """Create TrackingConfig from dictionary.

        enabled is intentionally NOT restored from disk. Scheduled monitoring is
        a live, in-session state, not a persisted preference: restoring it on
        reopen would either silently run unattended or show the toggle on while
        nothing is actually armed. The user re-enables each session. The cadence
        (interval_value/unit) is still restored.
        """
        return cls(
            enabled=False,
            interval_value=data.get("interval_value", 30),
            interval_unit=data.get("interval_unit", "minutes"),
            last_check=datetime.fromisoformat(data["last_check"]) if data.get("last_check") else None,
            next_check=datetime.fromisoformat(data["next_check"]) if data.get("next_check") else None,
        )


@dataclass
class ProjectConfig:
    """Configuration for a project, stored in project.json."""

    name: str
    platform: str
    created_at: datetime
    url_column: str
    screenshots_enabled: bool = False
    runs: list[RunConfig] = field(default_factory=list)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    # Monotonic allocator for mcat_index: the next number to hand a source URL.
    # Only ever increments, so a number is never reused even after deletes.
    next_url_index: int = 1

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "platform": self.platform,
            "created_at": self.created_at.isoformat(),
            "url_column": self.url_column,
            "screenshots_enabled": self.screenshots_enabled,
            "runs": [run.to_dict() for run in self.runs],
            "tracking": self.tracking.to_dict(),
            "next_url_index": self.next_url_index,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        """Create ProjectConfig from dictionary."""
        return cls(
            name=data["name"],
            platform=data["platform"],
            created_at=datetime.fromisoformat(data["created_at"]),
            url_column=data["url_column"],
            screenshots_enabled=data.get("screenshots_enabled", False),
            runs=[RunConfig.from_dict(r) for r in data.get("runs", [])],
            tracking=TrackingConfig.from_dict(data.get("tracking", {})),
            next_url_index=data.get("next_url_index", 1),
        )

    def save(self, path: Path) -> None:
        """Save configuration to JSON file."""
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        tmp_path.replace(path)

    @classmethod
    def load(cls, path: Path) -> "ProjectConfig":
        """Load configuration from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def add_run(self, run: RunConfig) -> None:
        """Add a run to the project."""
        self.runs.append(run)

    def get_run(self, run_id: str) -> RunConfig | None:
        """Get a run by ID."""
        for run in self.runs:
            if run.id == run_id:
                return run
        return None

    def get_interrupted_run(self) -> RunConfig | None:
        """Get the first interrupted run, if any."""
        for run in self.runs:
            if run.is_interrupted:
                return run
        return None

    def get_completed_runs(self) -> list[RunConfig]:
        """Get all completed runs."""
        return [run for run in self.runs if run.is_complete]

    @property
    def has_interrupted_run(self) -> bool:
        """Check if there's an interrupted run."""
        return self.get_interrupted_run() is not None

    @property
    def run_count(self) -> int:
        """Get total number of runs."""
        return len(self.runs)

    @property
    def completed_run_count(self) -> int:
        """Get number of completed runs."""
        return len(self.get_completed_runs())
