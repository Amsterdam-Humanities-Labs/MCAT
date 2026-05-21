"""
Service for managing processing runs within a project.
"""

import csv
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from utils.csv_handler import load_csv, save_csv
from models.project_models import RunConfig, RunStatus
from models.project_state import ProjectState


class RunService:

    def __init__(self, log_callback: Callable | None = None):
        self._log_callback: Callable | None = log_callback

    def set_log_callback(self, callback: Callable) -> None:
        self._log_callback = callback

    def _log(self, message: str, level: str = "info") -> None:
        if self._log_callback:
            self._log_callback(message, level)

    def generate_run_id(self, run_type: str = "manual") -> str:
        return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    def start_run(
        self,
        project_state: ProjectState,
        screenshots_enabled: bool = False,
        run_type: str = "manual"
    ) -> RunConfig:
        run_id = self.generate_run_id(run_type)

        run_path = project_state.get_run_path(run_id)
        run_path.mkdir(parents=True, exist_ok=True)

        if screenshots_enabled:
            screenshots_path = project_state.get_run_screenshots_path(run_id)
            screenshots_path.mkdir(parents=True, exist_ok=True)

        run = RunConfig(
            id=run_id,
            started_at=datetime.now(),
            status=RunStatus.IN_PROGRESS,
            screenshots_enabled=screenshots_enabled,
            run_type=run_type
        )

        project_state.config.add_run(run)
        project_state.save()
        project_state.current_run = run

        return run

    def complete_run(self, project_state: ProjectState, run: RunConfig) -> None:
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now()
        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()

        run.status_summary = self._compute_status_summary(project_state, run)
        run.total_checked = sum(run.status_summary.values())

        completed_runs = [r for r in project_state.config.get_completed_runs() if r.id != run.id]
        run.is_baseline = len(completed_runs) == 0

        if not run.is_baseline:
            previous_run = completed_runs[-1]
            changes = self._compute_changes(project_state, previous_run, run)
            run.changes_count = len(changes)
            run.changes_summary = self._summarize_changes(changes)
            self._write_changes_csv(project_state, run, changes)
        else:
            run.changes_count = 0
            run.changes_summary = {}

        project_state.current_run = None
        project_state.save()

    def abandon_run(self, project_state: ProjectState, run: RunConfig) -> None:
        run.status = RunStatus.ABANDONED
        run.completed_at = datetime.now()

        results_path = project_state.get_run_results_path(run.id)
        if results_path.exists():
            try:
                rows = load_csv(str(results_path))
                run.total_checked = len(rows)
            except Exception as e:
                self._log(f"Failed to read results for run {run.id}: {e}", "warning")

        if project_state.current_run and project_state.current_run.id == run.id:
            project_state.current_run = None

        project_state.save()

    def _compute_status_summary(self, project_state: ProjectState, run: RunConfig) -> dict[str, int]:
        results_path = project_state.get_run_results_path(run.id)
        summary = {"live": 0, "removed": 0, "restricted": 0, "error": 0, "unknown": 0, "login_required": 0}

        if not results_path.exists():
            return summary

        try:
            rows = load_csv(str(results_path))
            counts = Counter(r.get("mcat_status", "") for r in rows)
            summary["live"] = counts.get("Live", 0)
            summary["removed"] = counts.get("Removed", 0)
            summary["restricted"] = (
                counts.get("Restricted", 0)
                + counts.get("Age-restricted", 0)
                + counts.get("Geo-blocked", 0)
                + counts.get("Private", 0)
            )
            summary["error"] = counts.get("Error", 0)
            summary["unknown"] = counts.get("Unknown", 0)
            summary["login_required"] = counts.get("Login Required", 0)
        except Exception as e:
            self._log(f"Failed to compute status summary for run {run.id}: {e}", "warning")

        return summary

    def _compute_changes(self, project_state: ProjectState, previous_run: RunConfig, current_run: RunConfig) -> list[dict]:
        prev_path = project_state.get_run_results_path(previous_run.id)
        curr_path = project_state.get_run_results_path(current_run.id)

        if not prev_path.exists() or not curr_path.exists():
            return []

        try:
            prev_rows = load_csv(str(prev_path))
            curr_rows = load_csv(str(curr_path))
            url_col = project_state.url_column

            if not prev_rows or not curr_rows:
                return []
            if url_col not in prev_rows[0] or url_col not in curr_rows[0]:
                return []
            if "mcat_status" not in prev_rows[0] or "mcat_status" not in curr_rows[0]:
                return []

            prev_map = {r[url_col]: r["mcat_status"] for r in prev_rows}
            curr_map = {r[url_col]: r["mcat_status"] for r in curr_rows}

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

    def _summarize_changes(self, changes: list[dict]) -> dict[str, int]:
        summary: dict[str, int] = {}
        for ch in changes:
            key = f"{ch['previous_status'].lower()}_to_{ch['new_status'].lower()}"
            summary[key] = summary.get(key, 0) + 1
        return summary

    def _write_changes_csv(self, project_state: ProjectState, run: RunConfig, changes: list[dict]) -> None:
        changes_path = project_state.get_run_path(run.id) / "changes.csv"
        fieldnames = ["url", "previous_status", "new_status"]
        with open(changes_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(changes)

    def get_run_stats(self, project_state: ProjectState, run: RunConfig) -> dict[str, int]:
        return self._compute_status_summary(project_state, run)
