"""Processing handlers."""

from api.context import app_context, log_buffer
from api.serializers import publish_project
from models.project_models import RunStatus
from services.job_builder import build_processing_job


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

    def on_completed(result: object) -> None:
        if ctx.current_project and ctx.current_project.current_run:
            ctx.run_service.complete_run(ctx.current_project, ctx.current_project.current_run)
            log_buffer.success("Run completed")
        publish_project()

    def on_error(error_message: str) -> None:
        if ctx.current_project and ctx.current_project.current_run:
            ctx.current_project.current_run.status = RunStatus.ABANDONED
            ctx.current_project.current_run = None
            ctx.current_project.save()

    url_count = len(urls) if urls else job.file_info.row_count
    log_buffer.info(f"Starting run: {url_count} URLs on {project.platform}")

    success = ctx.processing_service.start_processing(
        job,
        urls=urls,
        on_completed=on_completed,
        on_error=on_error,
    )
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
