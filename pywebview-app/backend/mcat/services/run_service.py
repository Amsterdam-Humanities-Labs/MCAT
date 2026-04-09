"""
Service for managing processing runs within a project.

Handles run lifecycle: start, resume, complete, abandon.
Also generates combined.csv from completed runs.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import polars as pl

from models.project_models import RunConfig, RunStatus
from models.project_state import ProjectState


class RunService:
    """
    Service for managing processing runs.

    Responsibilities:
    - Start new runs (create folder, update project.json)
    - Complete/abandon run lifecycle
    - Generate combined.csv from completed runs
    """

    def __init__(self, log_callback=None):
        self._log_callback = log_callback

    def set_log_callback(self, callback):
        """Set the log callback for sending messages."""
        self._log_callback = callback

    def _log(self, message: str, level: str = "info"):
        """Log a message via callback if available."""
        if self._log_callback:
            self._log_callback(message, level)

    def generate_run_id(self, run_type: str = "manual") -> str:
        """
        Generate a unique run ID based on current timestamp.

        Returns:
            Run ID in format "YYYY-MM-DDTHH-MM"
        """
        return datetime.now().strftime("%Y-%m-%dT%H-%M")

    def start_run(
        self,
        project_state: ProjectState,
        screenshots_enabled: bool = False,
        run_type: str = "manual"
    ) -> RunConfig:
        """
        Start a new processing run.

        Creates run folder and updates project.json with new run entry.

        Args:
            project_state: Current project state
            screenshots_enabled: Whether to save screenshots
            run_type: Type of run ("manual" or "tracking")

        Returns:
            RunConfig for the new run
        """
        run_id = self.generate_run_id(run_type)

        # Create run folder
        run_path = project_state.get_run_path(run_id)
        run_path.mkdir(parents=True, exist_ok=True)

        # Create screenshots folder if enabled
        if screenshots_enabled:
            screenshots_path = project_state.get_run_screenshots_path(run_id)
            screenshots_path.mkdir(parents=True, exist_ok=True)

        # Create run config
        run = RunConfig(
            id=run_id,
            started_at=datetime.now(),
            status=RunStatus.IN_PROGRESS,
            screenshots_enabled=screenshots_enabled,
            run_type=run_type
        )

        # Add to project and save
        project_state.config.add_run(run)
        project_state.save()

        # Set as current run
        project_state.current_run = run

        return run

    def complete_run(self, project_state: ProjectState, run: RunConfig) -> None:
        """
        Mark a run as completed.

        Computes enriched metadata, generates changes.csv, and saves.
        """
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now()

        # Compute duration
        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()

        # Compute status summary from results.csv
        run.status_summary = self._compute_status_summary(project_state, run)
        run.total_checked = sum(run.status_summary.values())

        # Determine if baseline (first completed run, excluding this one)
        completed_runs = [r for r in project_state.config.get_completed_runs() if r.id != run.id]
        run.is_baseline = len(completed_runs) == 0

        # Compute changes against previous run
        if not run.is_baseline:
            previous_run = completed_runs[-1]
            changes = self._compute_changes(project_state, previous_run, run)
            run.changes_count = len(changes)
            run.changes_summary = self._summarize_changes(changes)
            self._write_changes_csv(project_state, run, changes)
        else:
            run.changes_count = 0
            run.changes_summary = {}

        # Clear current run
        project_state.current_run = None

        # Save project
        project_state.save()

    def abandon_run(self, project_state: ProjectState, run: RunConfig) -> None:
        """
        Mark a run as abandoned.

        The run data is preserved but won't be included in combined.csv.

        Args:
            project_state: Current project state
            run: The RunConfig to abandon
        """
        run.status = RunStatus.ABANDONED
        run.completed_at = datetime.now()

        # Count processed URLs from partial results
        results_path = project_state.get_run_results_path(run.id)
        if results_path.exists():
            try:
                df = pl.read_csv(results_path)
                run.total_checked = len(df)
            except Exception as e:
                self._log(f"Failed to read results for run {run.id}: {e}", "warning")

        # Clear current run if it's this one
        if project_state.current_run and project_state.current_run.id == run.id:
            project_state.current_run = None

        # Save project
        project_state.save()

    def _compute_status_summary(
        self,
        project_state: ProjectState,
        run: RunConfig
    ) -> dict:
        """Compute status breakdown from a run's results.csv."""
        results_path = project_state.get_run_results_path(run.id)
        summary = {"live": 0, "removed": 0, "restricted": 0, "error": 0}

        if not results_path.exists():
            return summary

        try:
            df = pl.read_csv(results_path)
            if "status" in df.columns:
                status_counts = df.group_by("status").len().to_dicts()
                counts = {row["status"]: row["len"] for row in status_counts}
                summary["live"] = counts.get("Live", 0)
                summary["removed"] = counts.get("Removed", 0)
                summary["restricted"] = (
                    counts.get("Restricted", 0)
                    + counts.get("Age-restricted", 0)
                    + counts.get("Geo-blocked", 0)
                    + counts.get("Private", 0)
                )
                summary["error"] = counts.get("Error", 0)
        except Exception as e:
            self._log(f"Failed to compute status summary for run {run.id}: {e}", "warning")

        return summary

    def _compute_changes(
        self,
        project_state: ProjectState,
        previous_run: RunConfig,
        current_run: RunConfig
    ) -> list[dict]:
        """Diff two runs and return list of changed URLs."""
        prev_path = project_state.get_run_results_path(previous_run.id)
        curr_path = project_state.get_run_results_path(current_run.id)

        if not prev_path.exists() or not curr_path.exists():
            return []

        try:
            prev_df = pl.read_csv(prev_path)
            curr_df = pl.read_csv(curr_path)
            url_col = project_state.url_column

            if url_col not in prev_df.columns or url_col not in curr_df.columns:
                return []
            if "status" not in prev_df.columns or "status" not in curr_df.columns:
                return []

            # Build url -> status maps
            prev_map = dict(zip(
                prev_df[url_col].cast(pl.Utf8).to_list(),
                prev_df["status"].cast(pl.Utf8).to_list()
            ))
            curr_map = dict(zip(
                curr_df[url_col].cast(pl.Utf8).to_list(),
                curr_df["status"].cast(pl.Utf8).to_list()
            ))

            changes = []
            for url, new_status in curr_map.items():
                old_status = prev_map.get(url)
                if old_status and old_status != new_status:
                    changes.append({
                        "url": url,
                        "previous_status": old_status,
                        "new_status": new_status,
                    })

            return changes
        except Exception as e:
            self._log(f"Failed to compute changes for run {current_run.id}: {e}", "warning")
            return []

    def _summarize_changes(self, changes: list[dict]) -> dict:
        """Summarize changes into transition counts like {'live_to_removed': 3}."""
        summary: dict[str, int] = {}
        for ch in changes:
            key = f"{ch['previous_status'].lower()}_to_{ch['new_status'].lower()}"
            summary[key] = summary.get(key, 0) + 1
        return summary

    def _write_changes_csv(
        self,
        project_state: ProjectState,
        run: RunConfig,
        changes: list[dict]
    ) -> None:
        """Write changes.csv for a run."""
        changes_path = project_state.get_run_path(run.id) / "changes.csv"
        if changes:
            df = pl.DataFrame(changes)
            df.write_csv(changes_path)
        else:
            # Write headers only
            pl.DataFrame(
                schema={"url": pl.Utf8, "previous_status": pl.Utf8, "new_status": pl.Utf8}
            ).write_csv(changes_path)

    def get_run_stats(
        self,
        project_state: ProjectState,
        run: RunConfig
    ) -> dict:
        """
        Get statistics for a run.

        Args:
            project_state: Current project state
            run: The RunConfig to get stats for

        Returns:
            Dictionary with stats (live, removed, restricted, errors counts)
        """
        results_path = project_state.get_run_results_path(run.id)
        stats = {'live': 0, 'removed': 0, 'restricted': 0, 'errors': 0}

        if not results_path.exists():
            return stats

        try:
            df = pl.read_csv(results_path)
            if 'status' in df.columns:
                status_counts = df.group_by('status').len().to_dicts()
                counts_dict = {row['status']: row['len'] for row in status_counts}
                stats['live'] = counts_dict.get('Live', 0)
                stats['removed'] = counts_dict.get('Removed', 0)
                stats['restricted'] = (
                    counts_dict.get('Restricted', 0) +
                    counts_dict.get('Age-restricted', 0) +
                    counts_dict.get('Geo-blocked', 0) +
                    counts_dict.get('Private', 0)
                )
                stats['errors'] = counts_dict.get('Error', 0)
        except Exception as e:
            self._log(f"Failed to read run stats for {run.id}: {e}", "warning")

        return stats
