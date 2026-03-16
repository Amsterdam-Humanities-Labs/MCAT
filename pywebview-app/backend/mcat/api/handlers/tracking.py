"""Tracking handlers for scheduled URL monitoring."""

from api.context import app_context, log_buffer


def start_tracking(body: dict) -> dict:
    """Start tracking scheduler for URL status monitoring."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    if not ctx.tracking_service:
        raise ValueError("Tracking service not initialized")

    interval_value = body.get("interval_value", 30)
    interval_unit = body.get("interval_unit", "minutes")

    result = ctx.tracking_service.start_tracking(ctx.current_project, interval_value, interval_unit)
    log_buffer.info(f"Tracking enabled: checks every {interval_value} {interval_unit}")

    return result


def stop_tracking(body: dict) -> dict:
    """Stop tracking scheduler."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    if not ctx.tracking_service:
        raise ValueError("Tracking service not initialized")

    result = ctx.tracking_service.stop_tracking(ctx.current_project)
    return result


def get_tracking_status(body: dict) -> dict:
    """Get current tracking status."""
    ctx = app_context
    if not ctx.current_project:
        return {
            "enabled": False,
            "interval_minutes": 60,
            "last_check": None,
            "next_check": None,
        }

    if not ctx.tracking_service:
        raise ValueError("Tracking service not initialized")

    return ctx.tracking_service.get_tracking_status(ctx.current_project)
