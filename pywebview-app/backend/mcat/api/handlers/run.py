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


def get_changed_results(body: dict) -> dict:
    """Get full result rows for URLs that changed status since previous run."""
    ctx = app_context
    if not ctx.current_project:
        raise ValueError("No project open")

    run_id = body.get("run_id")
    if not run_id:
        raise ValueError("Missing run_id")

    # Read changes to get the diff (url, previous_status, new_status)
    changes_path = ctx.current_project.get_run_path(run_id) / "changes.csv"
    if not changes_path.exists():
        return {"columns": [], "rows": []}

    changes_df = pl.read_csv(changes_path)
    if len(changes_df) == 0:
        return {"columns": [], "rows": []}

    # Build url -> previous_status map
    prev_map = dict(zip(
        changes_df["url"].cast(pl.Utf8).to_list(),
        changes_df["previous_status"].cast(pl.Utf8).to_list()
    ))

    # Read full results to get all columns for changed URLs
    results_path = ctx.current_project.get_run_results_path(run_id)
    if not results_path.exists():
        return {"columns": [], "rows": []}

    results_df = pl.read_csv(results_path)
    url_col = ctx.current_project.url_column

    # Filter results to only changed URLs
    changed_urls = list(prev_map.keys())
    filtered = results_df.filter(pl.col(url_col).cast(pl.Utf8).is_in(changed_urls))

    # Convert to dicts and add previous_status
    rows = filtered.to_dicts()
    for row in rows:
        url = str(row.get(url_col, ""))
        row["previous_status"] = prev_map.get(url, "")

    columns = ["previous_status"] + filtered.columns
    return {"columns": columns, "rows": rows}


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
