"""Shared serializers for building API/SSE payloads.

These live outside handlers so services can use them without
importing from the handler layer.
"""

from api.context import app_context
from events import event_bus
from cookies.cookie_store import CookieStore


def build_project_dict() -> dict | None:
    """Build project data dictionary for API responses and SSE events."""
    ctx = app_context
    if not ctx.current_project:
        return None

    project = ctx.current_project
    cookie_store = CookieStore(project.project_path)

    return {
        "name": project.name,
        "platform": project.platform,
        "path": str(project.project_path),
        "url_count": ctx.project_service.get_url_count(project),
        "url_column": project.url_column,
        "screenshots_enabled": project.config.screenshots_enabled,
        "runs": [run.to_dict() for run in project.config.runs],
        "tracking": project.config.tracking.to_dict(),
        "auth": cookie_store.get_auth_info(project.platform),
    }


def publish_project() -> None:
    """Publish project status via SSE."""
    event_bus.publish({
        "type": "project",
        "project": build_project_dict(),
    })
