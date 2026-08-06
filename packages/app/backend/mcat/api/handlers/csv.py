"""CSV operation handlers."""

from utils.csv_handler import load_csv, get_columns


def load(body: dict) -> dict:
    """Load CSV file and return columns."""
    path = body.get("path")
    if not path:
        raise ValueError("Missing path")

    rows = load_csv(path)
    return {
        "columns": get_columns(rows),
        "row_count": len(rows)
    }
