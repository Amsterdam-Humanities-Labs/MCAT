"""Processing handlers."""

import polars as pl

from api.context import app_context, log_buffer, event_bus
from models.processing_models import ProcessingJob
from models.file_models import FileInfo, ColumnMapping
from events import dispatcher, ProcessingEvents


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
        "pending": max(0, status.total_count - status.processed_count),
    }

    return {
        "state": status.state.value if status.state else "idle",
        "total": status.total_count,
        "processed": status.processed_count,
        "statusCounts": status_counts,
        "action": status.current_action,
        "error": status.error_message,
        "currentUrl": status.current_action.replace("Checking: ", "") if status.current_action and status.current_action.startswith("Checking: ") else None,
    }


def _publish_status():
    """Publish processing status via SSE."""
    event_bus.publish({
        "type": "processing",
        **_build_status_dict(),
    })


def _on_processing_progress(sender, **kwargs):
    """Handle processing progress - publish SSE event."""
    _publish_status()


def _on_processing_completed(sender, **kwargs):
    """Handle processing completion - complete the run and generate combined.csv."""
    ctx = app_context
    if ctx.current_project and ctx.current_project.current_run:
        run = ctx.current_project.current_run
        ctx.run_service.complete_run(ctx.current_project, run)
        log_buffer.success(f"Results saved to {ctx.current_project.combined_csv_path}")
    _publish_status()


def _on_processing_error(sender, **kwargs):
    """Handle processing error - mark run as failed."""
    ctx = app_context
    if ctx.current_project and ctx.current_project.current_run:
        run = ctx.current_project.current_run
        run.status = "failed"
        ctx.current_project.current_run = None
        ctx.current_project.save()
    _publish_status()


def _on_processing_paused(sender, **kwargs):
    """Handle processing paused."""
    _publish_status()


def _on_processing_resumed(sender, **kwargs):
    """Handle processing resumed."""
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
    screenshots = body.get("screenshots", False)

    # Start a new run
    run = ctx.run_service.start_run(project, screenshots_enabled=screenshots)
    output_folder = str(project.get_run_path(run.id))

    df = pl.read_csv(project.urls_csv_path)

    file_info = FileInfo(path=str(project.urls_csv_path))
    file_info.dataframe = df
    file_info.row_count = len(df)
    file_info.columns = df.columns
    file_info.valid = True

    column_mapping = ColumnMapping()
    column_mapping.post_column = project.url_column

    job = ProcessingJob(
        file_info=file_info,
        column_mapping=column_mapping,
        platform=project.platform,
        output_folder=output_folder,
        save_screenshots=screenshots
    )

    url_count = len(urls) if urls else len(df)
    log_buffer.info(f"Starting run {run.id}: {url_count} URLs on {project.platform}")

    success = ctx.processing_service.start_processing(job, urls=urls)
    if not success:
        log_buffer.error("Failed to start processing")
        # Abandon the run if start failed
        ctx.run_service.abandon_run(project, run)
    else:
        _publish_status()
    return {"success": success, "run_id": run.id}


def pause(body: dict) -> dict:
    """Pause processing."""
    ctx = app_context
    if not ctx.processing_service:
        raise ValueError("No processing service")

    success = ctx.processing_service.pause_processing()
    if success:
        log_buffer.warning("Processing paused")
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


def cancel(body: dict) -> dict:
    """Cancel processing."""
    ctx = app_context
    if not ctx.processing_service:
        raise ValueError("No processing service")

    success = ctx.processing_service.cancel_processing()
    if success:
        log_buffer.warning("Processing cancelled")
    return {"success": success}
