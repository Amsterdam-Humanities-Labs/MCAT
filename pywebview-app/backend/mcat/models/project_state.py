"""
Runtime state for an open project.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .project_models import ProjectConfig, RunConfig


@dataclass
class ProjectState:
    """
    Runtime state for an open project.

    Combines the persisted ProjectConfig with runtime information
    like paths and current run state.
    """

    config: ProjectConfig
    project_path: Path
    current_run: Optional[RunConfig] = None

    @property
    def name(self) -> str:
        """Get project name."""
        return self.config.name

    @property
    def platform(self) -> str:
        """Get project platform."""
        return self.config.platform

    @property
    def url_column(self) -> str:
        """Get URL column name."""
        return self.config.url_column

    @property
    def project_json_path(self) -> Path:
        """Get path to project.json."""
        return self.project_path / "project.json"

    @property
    def urls_csv_path(self) -> Path:
        """Get path to urls.csv."""
        return self.project_path / "urls.csv"

    @property
    def runs_path(self) -> Path:
        """Get path to runs directory."""
        return self.project_path / "runs"

    def get_run_path(self, run_id: str) -> Path:
        """Get path to a specific run directory."""
        return self.runs_path / run_id

    def get_run_results_path(self, run_id: str) -> Path:
        """Get path to a run's results.csv."""
        return self.get_run_path(run_id) / "results.csv"

    def get_run_screenshots_path(self, run_id: str) -> Path:
        """Get path to a run's screenshots directory."""
        return self.get_run_path(run_id) / "screenshots"

    @property
    def interrupted_run(self) -> Optional[RunConfig]:
        """Get the interrupted run, if any."""
        return self.config.get_interrupted_run()

    @property
    def has_interrupted_run(self) -> bool:
        """Check if there's an interrupted run."""
        return self.config.has_interrupted_run

    @property
    def is_running(self) -> bool:
        """Check if a run is currently active."""
        return self.current_run is not None

    def save(self) -> None:
        """Save the project configuration to disk."""
        self.config.save(self.project_json_path)

    @classmethod
    def load(cls, project_path: Path) -> "ProjectState":
        """Load project state from a project directory."""
        project_json_path = project_path / "project.json"
        config = ProjectConfig.load(project_json_path)
        return cls(config=config, project_path=project_path)
