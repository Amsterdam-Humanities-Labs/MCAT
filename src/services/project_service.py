"""
Service for project management operations.

Handles creating, opening, saving projects and importing URLs.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from models.project_models import ProjectConfig
from models.project_state import ProjectState
from models.import_result import UrlImportResult


class ProjectService:
    """
    Service for managing MCAT projects.

    Responsibilities:
    - Create new projects (folder structure, project.json, copy source CSV)
    - Open existing projects
    - Save project configuration
    - Import additional URLs with duplicate detection
    """

    def create_project(
        self,
        name: str,
        platform: str,
        location: Path,
        source_csv: Path,
        url_column: str,
        preserve_columns: list[str]
    ) -> ProjectState:
        """
        Create a new project.

        Args:
            name: Project name
            platform: Platform (youtube, instagram, etc.)
            location: Parent directory where project folder will be created
            source_csv: Path to source CSV file
            url_column: Name of column containing URLs
            preserve_columns: List of columns to preserve in output

        Returns:
            ProjectState for the newly created project

        Raises:
            FileExistsError: If project folder already exists
            ValueError: If source CSV is invalid
        """
        # Create project folder
        project_path = location / name
        if project_path.exists():
            raise FileExistsError(f"Project folder already exists: {project_path}")

        project_path.mkdir(parents=True)

        # Create runs directory
        runs_path = project_path / "runs"
        runs_path.mkdir()

        # Copy source CSV as urls.csv
        urls_csv_path = project_path / "urls.csv"
        shutil.copy(source_csv, urls_csv_path)

        # Validate the CSV has the required column
        df = pd.read_csv(urls_csv_path)
        if url_column not in df.columns:
            # Cleanup on failure
            shutil.rmtree(project_path)
            raise ValueError(f"URL column '{url_column}' not found in CSV")

        # Create project config
        config = ProjectConfig(
            name=name,
            platform=platform,
            created_at=datetime.now(),
            url_column=url_column,
            preserve_columns=preserve_columns,
            runs=[]
        )

        # Save project.json
        config.save(project_path / "project.json")

        return ProjectState(config=config, project_path=project_path)

    def open_project(self, project_path: Path) -> ProjectState:
        """
        Open an existing project.

        Args:
            project_path: Path to project folder

        Returns:
            ProjectState for the opened project

        Raises:
            FileNotFoundError: If project.json doesn't exist
            ValueError: If project structure is invalid
        """
        project_json_path = project_path / "project.json"
        if not project_json_path.exists():
            raise FileNotFoundError(f"project.json not found in {project_path}")

        urls_csv_path = project_path / "urls.csv"
        if not urls_csv_path.exists():
            raise ValueError(f"urls.csv not found in {project_path}")

        return ProjectState.load(project_path)

    def save_project(self, project_state: ProjectState) -> None:
        """
        Save project configuration to disk.

        Args:
            project_state: Current project state
        """
        project_state.save()

    def get_url_count(self, project_state: ProjectState) -> int:
        """
        Get the number of URLs in the project.

        Args:
            project_state: Current project state

        Returns:
            Number of URLs in urls.csv
        """
        df = pd.read_csv(project_state.urls_csv_path)
        return len(df)

    def get_urls(self, project_state: ProjectState) -> list[str]:
        """
        Get all URLs from the project.

        Args:
            project_state: Current project state

        Returns:
            List of URLs
        """
        df = pd.read_csv(project_state.urls_csv_path)
        return df[project_state.url_column].dropna().astype(str).tolist()

    def preview_url_import(
        self,
        project_state: ProjectState,
        csv_path: Path
    ) -> UrlImportResult:
        """
        Preview importing URLs from a CSV file.

        Detects duplicates and returns information about what would be imported.

        Args:
            project_state: Current project state
            csv_path: Path to CSV file to import

        Returns:
            UrlImportResult with preview information
        """
        result = UrlImportResult()

        try:
            # Load new CSV
            new_df = pd.read_csv(csv_path)

            # Check if URL column exists
            url_column = project_state.url_column
            if url_column not in new_df.columns:
                result.error_message = f"URL column '{url_column}' not found in CSV"
                return result

            # Get new URLs
            new_urls = set(new_df[url_column].dropna().astype(str).tolist())
            result.total_in_file = len(new_urls)

            # Get existing URLs
            existing_df = pd.read_csv(project_state.urls_csv_path)
            existing_urls = set(existing_df[url_column].dropna().astype(str).tolist())

            # Find duplicates and new URLs
            duplicates = new_urls & existing_urls
            urls_to_add = new_urls - existing_urls

            result.duplicates_skipped = len(duplicates)
            result.new_urls = len(urls_to_add)

            # Build rows to add (preserving all columns from new CSV that match)
            if urls_to_add:
                # Filter to only rows with new URLs
                mask = new_df[url_column].astype(str).isin(urls_to_add)
                rows_df = new_df[mask]

                # Keep only columns that exist in the project (url + preserve)
                columns_to_keep = [url_column] + [
                    col for col in project_state.preserve_columns
                    if col in new_df.columns
                ]
                rows_df = rows_df[columns_to_keep]

                result.rows_to_add = rows_df.to_dict('records')

        except Exception as e:
            result.error_message = str(e)

        return result

    def confirm_url_import(
        self,
        project_state: ProjectState,
        import_result: UrlImportResult
    ) -> int:
        """
        Confirm and execute URL import.

        Args:
            project_state: Current project state
            import_result: Result from preview_url_import

        Returns:
            Number of URLs added

        Raises:
            ValueError: If import_result is invalid
        """
        if not import_result.is_valid:
            raise ValueError("Invalid import result")

        if not import_result.rows_to_add:
            return 0

        # Load existing CSV
        existing_df = pd.read_csv(project_state.urls_csv_path)

        # Create DataFrame from rows to add
        new_rows_df = pd.DataFrame(import_result.rows_to_add)

        # Add missing columns with empty values
        for col in existing_df.columns:
            if col not in new_rows_df.columns:
                new_rows_df[col] = ""

        # Reorder columns to match existing
        new_rows_df = new_rows_df[existing_df.columns]

        # Append and save
        combined_df = pd.concat([existing_df, new_rows_df], ignore_index=True)
        combined_df.to_csv(project_state.urls_csv_path, index=False)

        return len(import_result.rows_to_add)

    def validate_project_structure(self, project_path: Path) -> tuple[bool, str]:
        """
        Validate a project folder has the required structure.

        Args:
            project_path: Path to project folder

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not project_path.exists():
            return False, "Project folder does not exist"

        project_json = project_path / "project.json"
        if not project_json.exists():
            return False, "project.json not found"

        urls_csv = project_path / "urls.csv"
        if not urls_csv.exists():
            return False, "urls.csv not found"

        runs_dir = project_path / "runs"
        if not runs_dir.exists():
            return False, "runs directory not found"

        return True, ""
