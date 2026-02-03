"""Project management handlers."""

from pathlib import Path
from api.context import app_context, event_bus


def _build_project_dict() -> dict | None:
    """Build project data dictionary."""
    ctx = app_context
    if not ctx.current_project:
        return None

    project = ctx.current_project
    return {
        "name": project.name,
        "platform": project.platform,
        "path": str(project.project_path),
        "combinedCsvPath": str(project.combined_csv_path),
        "urlCount": ctx.project_service.get_url_count(project),
        "urlColumn": project.url_column,
    }


def _publish_project():
    """Publish project status via SSE."""
    event_bus.publish({
        "type": "project",
        "project": _build_project_dict(),
    })


def create(body: dict) -> dict:
    """Create a new project."""
    required = ["name", "platform", "location", "csv_path", "url_column"]
    for field in required:
        if field not in body:
            raise ValueError(f"Missing required field: {field}")

    ctx = app_context
    project = ctx.project_service.create_project(
        name=body["name"],
        platform=body["platform"],
        location=Path(body["location"]),
        source_csv=Path(body["csv_path"]),
        url_column=body["url_column"],
        preserve_columns=body.get("preserve_columns", [])
    )
    ctx.set_project(project)
    _publish_project()
    return {"success": True, "project_path": str(project.project_path)}


def open_project(body: dict) -> dict:
    """Open an existing project."""
    if "path" not in body:
        raise ValueError("Missing required field: path")

    ctx = app_context
    path = Path(body["path"])
    if path.name == "project.json":
        path = path.parent
    project = ctx.project_service.open_project(path)
    ctx.set_project(project)
    _publish_project()
    return {"success": True, "name": project.name}


def close() -> dict:
    """Close current project."""
    app_context.close_project()
    _publish_project()
    return {"success": True}


def preview_import(body: dict) -> dict:
    """Preview import from CSV."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    csv_path = body.get("csv_path")
    if not csv_path:
        raise ValueError("Missing csv_path")

    result = ctx.project_service.preview_url_import(
        ctx.current_project,
        Path(csv_path)
    )

    if result.has_error:
        raise ValueError(result.error_message)

    ctx._pending_import = result

    return {
        "total_in_file": result.total_in_file,
        "new_urls": result.new_urls,
        "duplicates_skipped": result.duplicates_skipped,
        "sample_urls": [
            row.get(ctx.current_project.url_column, "")
            for row in result.rows_to_add[:10]
        ] if result.rows_to_add else []
    }


def confirm_import(body: dict) -> dict:
    """Confirm and execute import."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    if not ctx._pending_import:
        raise ValueError("No pending import")

    added = ctx.project_service.confirm_url_import(
        ctx.current_project,
        ctx._pending_import
    )
    ctx._pending_import = None
    _publish_project()
    return {"added": added}
