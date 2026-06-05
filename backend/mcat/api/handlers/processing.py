"""Processing handlers."""

from api.context import app_context, log_buffer
from api.serializers import publish_project
from api.handlers.auth import login_in_progress
from services.job_builder import build_processing_job


def start(body: dict) -> dict:
    """Start processing."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    if not ctx.processing_service:
        raise ValueError("Processing service not initialized")

    # A Set up browser capture writes its cookies on window close, slightly after
    # the window disappears. Starting now would load the jar before those cookies
    # land, so the run would scrape without them (e.g. the consent modal returns).
    if login_in_progress():
        return {"success": False, "error": "Browser setup is finishing, try again in a moment"}

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
        # Delegate to the canonical lifecycle method so the failed run still gets
        # completed_at / total_checked and reappears in the timeline, then surface
        # the reason. Hand-rolling abandonment here skipped all of that.
        if ctx.current_project and ctx.current_project.current_run:
            ctx.run_service.abandon_run(ctx.current_project, ctx.current_project.current_run)
        log_buffer.error(error_message)
        publish_project()

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


def abandon(body: dict) -> dict:
    """Abandon the active (running or paused) run.

    Stops the live workers via cancel_processing() — which on its own leaves the
    run record dangling in_progress, because the cancelled worker never fires its
    on_completed callback — then finalizes the current run as abandoned, keeping
    whatever partial results were already written. publish_project() refreshes the
    timeline; cancel_processing() already pushed the CANCELLED state so the UI
    returns to idle.
    """
    ctx = app_context
    if not ctx.processing_service:
        raise ValueError("No processing service")

    success = ctx.processing_service.cancel_processing()

    if ctx.current_project and ctx.current_project.current_run:
        ctx.run_service.abandon_run(ctx.current_project, ctx.current_project.current_run)
        log_buffer.info("Run abandoned")

    publish_project()
    return {"success": success}
