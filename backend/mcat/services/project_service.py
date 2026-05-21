"""
Service for project management operations.
"""

import shutil
from datetime import datetime
from pathlib import Path

from utils.csv_handler import load_csv, save_csv, get_columns
from models.project_models import ProjectConfig
from models.project_state import ProjectState
from models.import_result import UrlImportResult


class ProjectService:

    def create_project(
        self,
        name: str,
        platform: str,
        location: Path,
        source_csv: Path,
        url_column: str,
    ) -> ProjectState:
        project_path = location / name
        if project_path.exists():
            raise FileExistsError(f"Project folder already exists: {project_path}")

        project_path.mkdir(parents=True)

        runs_path = project_path / "runs"
        runs_path.mkdir()

        urls_csv_path = project_path / "urls.csv"
        shutil.copy(source_csv, urls_csv_path)

        rows = load_csv(str(urls_csv_path))
        columns = get_columns(rows)
        if url_column not in columns:
            shutil.rmtree(project_path)
            raise ValueError(f"URL column '{url_column}' not found in CSV")

        config = ProjectConfig(
            name=name,
            platform=platform,
            created_at=datetime.now(),
            url_column=url_column,
            runs=[]
        )

        config.save(project_path / "project.json")

        return ProjectState(config=config, project_path=project_path)

    def open_project(self, project_path: Path) -> ProjectState:
        project_json_path = project_path / "project.json"
        if not project_json_path.exists():
            raise FileNotFoundError(f"project.json not found in {project_path}")

        urls_csv_path = project_path / "urls.csv"
        if not urls_csv_path.exists():
            raise ValueError(f"urls.csv not found in {project_path}")

        return ProjectState.load(project_path)

    def save_project(self, project_state: ProjectState) -> None:
        project_state.save()

    def get_url_count(self, project_state: ProjectState) -> int:
        rows = load_csv(str(project_state.urls_csv_path))
        return len(rows)

    def get_urls(self, project_state: ProjectState) -> list[str]:
        rows = load_csv(str(project_state.urls_csv_path))
        return [r[project_state.url_column] for r in rows if r.get(project_state.url_column)]

    def preview_url_import(self, project_state: ProjectState, csv_path: Path) -> UrlImportResult:
        result = UrlImportResult()

        try:
            new_rows = load_csv(str(csv_path))
            url_column = project_state.url_column

            new_columns = get_columns(new_rows)
            if url_column not in new_columns:
                result.error_message = f"URL column '{url_column}' not found in CSV"
                return result

            new_urls = set(r[url_column] for r in new_rows if r.get(url_column))
            result.total_in_file = len(new_urls)

            existing_rows = load_csv(str(project_state.urls_csv_path))
            existing_urls = set(r[url_column] for r in existing_rows if r.get(url_column))

            duplicates = new_urls & existing_urls
            urls_to_add = new_urls - existing_urls

            result.duplicates_skipped = len(duplicates)
            result.new_urls = len(urls_to_add)

            if urls_to_add:
                result.rows_to_add = [r for r in new_rows if r.get(url_column) in urls_to_add]

        except Exception as e:
            result.error_message = str(e)

        return result

    def confirm_url_import(self, project_state: ProjectState, import_result: UrlImportResult) -> int:
        if not import_result.is_valid:
            raise ValueError("Invalid import result")

        if not import_result.rows_to_add:
            return 0

        existing_rows = load_csv(str(project_state.urls_csv_path))
        existing_columns = get_columns(existing_rows)

        for row in import_result.rows_to_add:
            padded = {col: row.get(col, "") for col in existing_columns}
            existing_rows.append(padded)

        save_csv(existing_rows, str(project_state.urls_csv_path))

        return len(import_result.rows_to_add)

    def validate_project_structure(self, project_path: Path) -> tuple[bool, str]:
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
