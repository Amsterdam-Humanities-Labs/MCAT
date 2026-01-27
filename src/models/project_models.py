"""
Data models for project management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional
import json


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
    completed_at: Optional[datetime] = None
    status: RunStatus = RunStatus.IN_PROGRESS
    screenshots_enabled: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "screenshots_enabled": self.screenshots_enabled
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RunConfig":
        """Create RunConfig from dictionary."""
        return cls(
            id=data["id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            status=RunStatus(data["status"]),
            screenshots_enabled=data.get("screenshots_enabled", False)
        )

    @property
    def is_complete(self) -> bool:
        """Check if run is complete."""
        return self.status == RunStatus.COMPLETED

    @property
    def is_interrupted(self) -> bool:
        """Check if run was interrupted (still in progress but not running)."""
        return self.status == RunStatus.IN_PROGRESS


@dataclass
class ProjectConfig:
    """Configuration for a project, stored in project.json."""

    name: str
    platform: str
    created_at: datetime
    url_column: str
    preserve_columns: List[str] = field(default_factory=list)
    runs: List[RunConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "platform": self.platform,
            "created_at": self.created_at.isoformat(),
            "url_column": self.url_column,
            "preserve_columns": self.preserve_columns,
            "runs": [run.to_dict() for run in self.runs]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectConfig":
        """Create ProjectConfig from dictionary."""
        return cls(
            name=data["name"],
            platform=data["platform"],
            created_at=datetime.fromisoformat(data["created_at"]),
            url_column=data["url_column"],
            preserve_columns=data.get("preserve_columns", []),
            runs=[RunConfig.from_dict(r) for r in data.get("runs", [])]
        )

    def save(self, path: Path) -> None:
        """Save configuration to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ProjectConfig":
        """Load configuration from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def add_run(self, run: RunConfig) -> None:
        """Add a run to the project."""
        self.runs.append(run)

    def get_run(self, run_id: str) -> Optional[RunConfig]:
        """Get a run by ID."""
        for run in self.runs:
            if run.id == run_id:
                return run
        return None

    def get_interrupted_run(self) -> Optional[RunConfig]:
        """Get the first interrupted run, if any."""
        for run in self.runs:
            if run.is_interrupted:
                return run
        return None

    def get_completed_runs(self) -> List[RunConfig]:
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
