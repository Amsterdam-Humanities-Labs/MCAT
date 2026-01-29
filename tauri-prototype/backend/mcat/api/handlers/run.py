"""Run management handlers."""

from api.context import app_context


def start(body: dict) -> dict:
    """Start a new run."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    run = ctx.run_service.start_run(
        ctx.current_project,
        screenshots_enabled=body.get("screenshots", False)
    )
    return {"success": True, "run_id": run.id}


def complete(body: dict) -> dict:
    """Complete current run."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    if not ctx.current_project.current_run:
        raise ValueError("No active run")

    ctx.run_service.complete_run(
        ctx.current_project,
        ctx.current_project.current_run
    )
    return {"success": True}


def get_stats() -> dict:
    """Get current run stats."""
    ctx = app_context
    if not ctx.current_project:
        return {"stats": None}

    if not ctx.current_project.current_run:
        return {"stats": None}

    stats = ctx.run_service.get_run_stats(
        ctx.current_project,
        ctx.current_project.current_run
    )
    return {"stats": stats}


def get_interrupted() -> dict:
    """Check for interrupted runs."""
    ctx = app_context
    if not ctx.current_project:
        return {"has_interrupted": False}

    try:
        interrupted = ctx.current_project.config.get_interrupted_run()
        if interrupted:
            processed_count = ctx.run_service.get_processed_count(
                ctx.current_project, interrupted
            )
            total_count = ctx.project_service.get_url_count(ctx.current_project)
            return {
                "has_interrupted": True,
                "run": {
                    "run_id": interrupted.id,
                    "processed": processed_count,
                    "total": total_count,
                    "remaining": total_count - processed_count
                }
            }
        else:
            return {"has_interrupted": False}
    except Exception:
        return {"has_interrupted": False}


def resume_run(body: dict) -> dict:
    """Resume an interrupted run."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    run_id = body.get("run_id")
    if not run_id:
        raise ValueError("Missing run_id")

    run = ctx.current_project.config.get_run(run_id)
    if not run:
        raise ValueError(f"Run not found: {run_id}")

    run, remaining = ctx.run_service.resume_run(ctx.current_project, run)
    return {"success": True, "remaining_urls": remaining}


def abandon(body: dict) -> dict:
    """Abandon an interrupted run."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    run_id = body.get("run_id")
    if not run_id:
        raise ValueError("Missing run_id")

    run = ctx.current_project.config.get_run(run_id)
    if not run:
        raise ValueError(f"Run not found: {run_id}")

    ctx.run_service.abandon_run(ctx.current_project, run)
    return {"success": True}
