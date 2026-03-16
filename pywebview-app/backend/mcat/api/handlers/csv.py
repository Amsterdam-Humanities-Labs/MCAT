"""CSV operation handlers."""

import polars as pl


def load(body: dict) -> dict:
    """Load CSV file and return columns."""
    path = body.get("path")
    if not path:
        raise ValueError("Missing path")

    df = pl.read_csv(path)
    return {
        "columns": df.columns,
        "row_count": len(df)
    }


def detect_url_column(body: dict) -> dict:
    """Detect URL column from column names."""
    columns = body.get("columns", [])

    url_patterns = ["url", "link", "post_url", "video_url", "content_url", "href"]
    candidates = []
    recommended = None

    for col in columns:
        col_lower = col.lower()
        for pattern in url_patterns:
            if pattern in col_lower:
                candidates.append(col)
                if pattern == "url" or col_lower == pattern:
                    recommended = col
                break

    if not recommended and candidates:
        recommended = candidates[0]

    return {
        "candidates": candidates,
        "recommended": recommended
    }
