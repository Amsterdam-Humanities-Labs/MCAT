"""Run management handlers."""

import polars as pl

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


def get_changes(body: dict) -> dict:
    """Get changes.csv data for a run."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    run_id = body.get("run_id")
    if not run_id:
        raise ValueError("Missing run_id")

    changes_path = ctx.current_project.get_run_path(run_id) / "changes.csv"
    if not changes_path.exists():
        return {"changes": []}

    df = pl.read_csv(changes_path)
    return {"changes": df.to_dicts()}


def get_results(body: dict) -> dict:
    """Get results.csv data for a run."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    run_id = body.get("run_id")
    if not run_id:
        raise ValueError("Missing run_id")

    results_path = ctx.current_project.get_run_results_path(run_id)
    if not results_path.exists():
        return {"columns": [], "rows": []}

    df = pl.read_csv(results_path)
    return {"columns": df.columns, "rows": df.to_dicts()}
