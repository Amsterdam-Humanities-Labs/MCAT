"""Run management handlers."""

from api.context import app_context


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
