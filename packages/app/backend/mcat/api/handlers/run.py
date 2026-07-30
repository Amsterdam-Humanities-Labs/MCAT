"""Run management handlers."""

from api.context import app_context
from utils.csv_handler import load_csv, get_columns


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

    changes_path = ctx.current_project.get_run_path(run_id) / "changes.csv"
    if not changes_path.exists():
        return {"columns": [], "rows": []}

    change_rows = load_csv(str(changes_path))
    if not change_rows:
        return {"columns": [], "rows": []}

    prev_map = {r["url"]: r["previous_status"] for r in change_rows}

    results_path = ctx.current_project.get_run_results_path(run_id)
    if not results_path.exists():
        return {"columns": [], "rows": []}

    result_rows = load_csv(str(results_path))
    url_col = ctx.current_project.url_column

    changed_urls = set(prev_map.keys())
    filtered = [r for r in result_rows if r.get(url_col) in changed_urls]

    for row in filtered:
        url = row.get(url_col, "")
        row["previous_status"] = prev_map.get(url, "")

    columns = ["previous_status"] + get_columns(result_rows)
    return {"columns": columns, "rows": filtered}


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

    rows = load_csv(str(results_path))
    return {"columns": get_columns(rows), "rows": rows}
