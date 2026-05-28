"""Processing handlers."""

from api.context import app_context, log_buffer, event_bus
from api.serializers import publish_project
from models.project_models import RunStatus
from events import dispatcher, ProcessingEvents
from services.job_builder import build_processing_job


def _build_status_dict() -> dict:
    """Build processing status dictionary."""
    ctx = app_context
    if not ctx.processing_service:
        return {"state": "no_project"}

    ctx.processing_service._process_progress_updates()
    status = ctx.processing_service.get_current_status()

    stats = status.stats or {}
    status_counts = {
        "live": stats.get("live", 0),
        "removed": stats.get("removed", 0),
        "restricted": stats.get("restricted", 0),
        "error": stats.get("errors", 0),
    }

    return {
        "state": status.state.value if status.state else "idle",
        "total": status.total_count,
        "processed": status.processed_count,
        "status_counts": status_counts,
        "action": status.current_action,
        "error": status.error_message,
        "current_url": status.current_action.replace("Checking: ", "") if status.current_action and status.current_action.startswith("Checking: ") else None,
    }


def _publish_status() -> None:
    """Publish processing status via SSE."""
    event_bus.publish({
        "type": "processing",
        **_build_status_dict(),
    })


def _is_stale(sender: object) -> bool:
    """Check if signal came from an orphaned processing service."""
    return sender is not app_context.processing_service


def _on_processing_progress(sender: object, **kwargs: object) -> None:
    if _is_stale(sender):
        return
    _publish_status()


def _on_processing_completed(sender: object, **kwargs: object) -> None:
    if _is_stale(sender):
        return
    ctx = app_context
    if ctx.current_project and ctx.current_project.current_run:
        run = ctx.current_project.current_run
        ctx.run_service.complete_run(ctx.current_project, run)
        log_buffer.success("Run completed")
    _publish_status()
    publish_project()


def _on_processing_error(sender: object, **kwargs: object) -> None:
    if _is_stale(sender):
        return
    ctx = app_context
    if ctx.current_project and ctx.current_project.current_run:
        run = ctx.current_project.current_run
        run.status = RunStatus.ABANDONED
        ctx.current_project.current_run = None
        ctx.current_project.save()
    _publish_status()


def _on_processing_paused(sender: object, **kwargs: object) -> None:
    if _is_stale(sender):
        return
    _publish_status()


def _on_processing_resumed(sender: object, **kwargs: object) -> None:
    if _is_stale(sender):
        return
    _publish_status()


# Register event handlers
dispatcher.connect(_on_processing_progress, signal=ProcessingEvents.PROGRESS)
dispatcher.connect(_on_processing_completed, signal=ProcessingEvents.COMPLETED)
dispatcher.connect(_on_processing_error, signal=ProcessingEvents.ERROR)
dispatcher.connect(_on_processing_paused, signal=ProcessingEvents.PAUSED)
dispatcher.connect(_on_processing_resumed, signal=ProcessingEvents.RESUMED)


def start(body: dict) -> dict:
    """Start processing."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    if not ctx.processing_service:
        raise ValueError("Processing service not initialized")

    urls = body.get("urls")
    project = ctx.current_project
    screenshots = project.config.screenshots_enabled

    run = ctx.run_service.start_run(project, screenshots_enabled=screenshots)
    output_folder = str(project.get_run_path(run.id))

    job = build_processing_job(project, output_folder, screenshots)

    url_count = len(urls) if urls else job.file_info.row_count
    log_buffer.info(f"Starting run: {url_count} URLs on {project.platform}")

    success = ctx.processing_service.start_processing(job, urls=urls)
    if not success:
        log_buffer.error("Failed to start processing")
        ctx.run_service.abandon_run(project, run)
    return {"success": success, "run_id": run.id}


def pause(body: dict) -> dict:
    """Pause processing."""
    ctx = app_context
    if not ctx.processing_service:
        raise ValueError("No processing service")

    success = ctx.processing_service.pause_processing()
    if success:
        log_buffer.info("Processing paused")
    return {"success": success}


def resume(body: dict) -> dict:
    """Resume processing."""
    ctx = app_context
    if not ctx.processing_service:
        raise ValueError("No processing service")

    success = ctx.processing_service.resume_processing()
    if success:
        log_buffer.info("Processing resumed")
    return {"success": success}
