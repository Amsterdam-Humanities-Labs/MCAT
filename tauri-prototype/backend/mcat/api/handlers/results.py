"""Results handlers."""

import polars as pl

from api.context import app_context


def get_combined() -> dict:
    """Get combined results with status counts."""
    ctx = app_context
    if not ctx.current_project:
        return {
            "results": [],
            "by_status": {"live": 0, "removed": 0, "restricted": 0, "error": 0, "pending": 0}
        }

    try:
        results = []
        status_counts = {"live": 0, "removed": 0, "restricted": 0, "error": 0, "pending": 0}

        results_path = ctx.current_project.combined_csv_path
        url_column = ctx.current_project.url_column
        if results_path.exists():
            df = pl.read_csv(results_path)

            for row in df.to_dicts():
                status = str(row.get("status", "pending")).lower()
                if status not in status_counts:
                    status = "error"

                status_counts[status] += 1

                # Include all columns, with url mapped to standard key
                result_row = dict(row)
                result_row["url"] = row.get(url_column, "")
                result_row["status"] = status
                results.append(result_row)

        return {
            "results": results,
            "by_status": status_counts
        }
    except Exception:
        return {
            "results": [],
            "by_status": {"live": 0, "removed": 0, "restricted": 0, "error": 0, "pending": 0}
        }
