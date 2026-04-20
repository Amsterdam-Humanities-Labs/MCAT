"""Health check handler."""

from api.context import app_context


def get_health() -> dict:
    """Health check endpoint."""
    ctx = app_context
    return {
        "status": "ok",
        "has_project": ctx.current_project is not None,
        "is_processing": ctx.processing_service.is_processing() if ctx.processing_service else False
    }
