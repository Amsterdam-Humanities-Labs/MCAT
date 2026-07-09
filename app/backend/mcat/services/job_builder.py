"""Shared logic for building ProcessingJob from project state."""

from cookies.cookie_store import CookieStore
from models.file_models import FileInfo, ColumnMapping
from models.processing_models import ProcessingJob
from models.project_state import ProjectState
from utils.csv_handler import load_csv, get_columns


def build_processing_job(
    project: ProjectState,
    output_folder: str,
    screenshots: bool = False,
) -> ProcessingJob:
    """Build a ProcessingJob from project state.

    Used by both manual start and tracking runs to ensure
    consistent job construction.
    """
    rows = load_csv(str(project.urls_csv_path))

    file_info = FileInfo(path=str(project.urls_csv_path))
    file_info.rows = rows
    file_info.row_count = len(rows)
    file_info.columns = get_columns(rows)
    file_info.valid = True

    column_mapping = ColumnMapping()
    column_mapping.post_column = project.url_column

    cookie_store = CookieStore(project.project_path)
    cookies = cookie_store.load_cookies(project.platform) or []
    cookie_info = cookie_store.get_cookie_info(project.platform)
    # Account id (IG/FB) if the platform exposes one; else "logged-in" for an
    # authenticated run with no readable id (YouTube/Google); else anonymous.
    if cookie_info and cookie_info["username"]:
        auth_user = cookie_info["username"]
    elif cookie_info and cookie_info.get("logged_in"):
        auth_user = "logged-in"
    else:
        auth_user = "anonymous"

    return ProcessingJob(
        file_info=file_info,
        column_mapping=column_mapping,
        platform=project.platform,
        output_folder=output_folder,
        save_screenshots=screenshots,
        cookies=cookies,
        auth_user=auth_user,
    )
