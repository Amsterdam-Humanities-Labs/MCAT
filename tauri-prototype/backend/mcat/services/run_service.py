"""
Service for managing processing runs within a project.

Handles run lifecycle: start, resume, complete, abandon.
Also generates combined.csv from completed runs.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from models.project_models import RunConfig, RunStatus
from models.project_state import ProjectState


class RunService:
    """
    Service for managing processing runs.

    Responsibilities:
    - Start new runs (create folder, update project.json)
    - Resume interrupted runs (detect processed URLs, continue)
    - Complete/abandon run lifecycle
    - Generate combined.csv from completed runs
    """

    def generate_run_id(self) -> str:
        """
        Generate a unique run ID based on current timestamp.

        Returns:
            Run ID in format "YYYY-MM-DDTHH-MM"
        """
        return datetime.now().strftime("%Y-%m-%dT%H-%M")

    def start_run(
        self,
        project_state: ProjectState,
        screenshots_enabled: bool = False
    ) -> RunConfig:
        """
        Start a new processing run.

        Creates run folder and updates project.json with new run entry.

        Args:
            project_state: Current project state
            screenshots_enabled: Whether to save screenshots

        Returns:
            RunConfig for the new run
        """
        run_id = self.generate_run_id()

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
            screenshots_enabled=screenshots_enabled
        )

        # Add to project and save
        project_state.config.add_run(run)
        project_state.save()

        # Set as current run
        project_state.current_run = run

        return run

    def resume_run(
        self,
        project_state: ProjectState,
        run: RunConfig
    ) -> tuple[RunConfig, list[str]]:
        """
        Resume an interrupted run.

        Detects which URLs were already processed and returns remaining URLs.

        Args:
            project_state: Current project state
            run: The interrupted RunConfig to resume

        Returns:
            Tuple of (RunConfig, remaining_urls)
        """
        # Get processed URLs from partial results
        processed_urls = self.get_processed_urls(project_state, run)

        # Get all URLs from project
        all_urls_df = pd.read_csv(project_state.urls_csv_path)
        all_urls = set(all_urls_df[project_state.url_column].dropna().astype(str).tolist())

        # Calculate remaining
        remaining_urls = list(all_urls - processed_urls)

        # Set as current run
        project_state.current_run = run

        return run, remaining_urls

    def complete_run(self, project_state: ProjectState, run: RunConfig) -> None:
        """
        Mark a run as completed.

        Updates status and regenerates combined.csv.

        Args:
            project_state: Current project state
            run: The RunConfig to complete
        """
        run.status = RunStatus.COMPLETED
        run.completed_at = datetime.now()

        # Clear current run
        project_state.current_run = None

        # Save project
        project_state.save()

        # Regenerate combined.csv
        self.generate_combined_csv(project_state)

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

        # Clear current run if it's this one
        if project_state.current_run and project_state.current_run.id == run.id:
            project_state.current_run = None

        # Save project
        project_state.save()

    def get_processed_urls(
        self,
        project_state: ProjectState,
        run: RunConfig
    ) -> set[str]:
        """
        Get URLs that were already processed in a run.

        Args:
            project_state: Current project state
            run: The RunConfig to check

        Returns:
            Set of processed URLs
        """
        results_path = project_state.get_run_results_path(run.id)

        if not results_path.exists():
            return set()

        try:
            df = pd.read_csv(results_path)
            url_column = project_state.url_column
            if url_column in df.columns:
                return set(df[url_column].dropna().astype(str).tolist())
        except Exception:
            pass

        return set()

    def get_processed_count(
        self,
        project_state: ProjectState,
        run: RunConfig
    ) -> int:
        """
        Get count of processed URLs in a run.

        Args:
            project_state: Current project state
            run: The RunConfig to check

        Returns:
            Number of processed URLs
        """
        return len(self.get_processed_urls(project_state, run))

    def get_remaining_urls(
        self,
        project_state: ProjectState,
        run: RunConfig
    ) -> list[str]:
        """
        Get URLs that still need to be processed in a run.

        Args:
            project_state: Current project state
            run: The RunConfig to check

        Returns:
            List of remaining URLs
        """
        # Get all URLs
        all_urls_df = pd.read_csv(project_state.urls_csv_path)
        all_urls = set(all_urls_df[project_state.url_column].dropna().astype(str).tolist())

        # Get processed URLs
        processed_urls = self.get_processed_urls(project_state, run)

        # Return remaining
        return list(all_urls - processed_urls)

    def generate_combined_csv(self, project_state: ProjectState) -> Path:
        """
        Generate combined.csv from all completed runs.

        Only includes runs with status COMPLETED.

        Args:
            project_state: Current project state

        Returns:
            Path to generated combined.csv
        """
        completed_runs = project_state.config.get_completed_runs()

        if not completed_runs:
            # Create empty combined.csv with headers
            combined_path = project_state.combined_csv_path
            # Get columns from urls.csv
            urls_df = pd.read_csv(project_state.urls_csv_path)
            result_columns = ['status', 'info', 'screenshot_path', 'timestamp', 'error_message', 'run_id']
            all_columns = list(urls_df.columns) + result_columns
            empty_df = pd.DataFrame(columns=all_columns)
            empty_df.to_csv(combined_path, index=False)
            return combined_path

        # Collect all results
        all_results = []

        for run in completed_runs:
            results_path = project_state.get_run_results_path(run.id)
            if results_path.exists():
                try:
                    df = pd.read_csv(results_path)
                    df['run_id'] = run.id
                    all_results.append(df)
                except Exception as e:
                    print(f"Warning: Could not read {results_path}: {e}")

        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
        else:
            # No results, create empty DataFrame
            urls_df = pd.read_csv(project_state.urls_csv_path)
            result_columns = ['status', 'info', 'screenshot_path', 'timestamp', 'error_message', 'run_id']
            all_columns = list(urls_df.columns) + result_columns
            combined_df = pd.DataFrame(columns=all_columns)

        # Save
        combined_path = project_state.combined_csv_path
        combined_df.to_csv(combined_path, index=False)

        return combined_path

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
            df = pd.read_csv(results_path)
            if 'status' in df.columns:
                status_counts = df['status'].value_counts().to_dict()
                stats['live'] = status_counts.get('Live', 0)
                stats['removed'] = status_counts.get('Removed', 0)
                stats['restricted'] = (
                    status_counts.get('Restricted', 0) +
                    status_counts.get('Age-restricted', 0) +
                    status_counts.get('Geo-blocked', 0) +
                    status_counts.get('Private', 0)
                )
                stats['errors'] = status_counts.get('Error', 0)
        except Exception:
            pass

        return stats
