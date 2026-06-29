import csv
import os
import threading
from collections import Counter

from models.types import StatusSummary


def load_csv(file_path: str) -> list[dict]:
    """Load a CSV with automatic delimiter detection. Returns a list of dicts.

    Tries each delimiter and returns the first that splits into more than one
    column. A genuinely single-column file (e.g. just URLs) falls back to the
    first successful parse.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    fallback = None
    for separator in [',', ';', '\t', '|']:
        try:
            with open(file_path, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=separator)
                rows = list(reader)
        except Exception:
            continue
        if not reader.fieldnames:
            continue
        if len(reader.fieldnames) > 1:
            return rows
        if fallback is None:
            fallback = rows

    if fallback is not None:
        return fallback

    raise Exception(f"Error loading CSV file: {file_path}")


def save_csv(rows: list[dict], output_path: str) -> None:
    """Save list of dicts to CSV file."""
    if not rows:
        return
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def get_columns(rows: list[dict]) -> list[str]:
    """Get column names from a list of dicts."""
    if not rows:
        return []
    return list(rows[0].keys())


def normalize_url(url: str) -> str:
    """Prepend https:// if no scheme is present."""
    url = url.strip()
    if not url:
        return url
    if "://" not in url:
        url = "https://" + url
    return url


def get_urls_from_column(rows: list[dict], url_column: str) -> list[str]:
    """Extract non-empty URLs from the specified column, normalized."""
    urls = [normalize_url(r[url_column]) for r in rows if r.get(url_column)]
    if not urls:
        raise ValueError(f"No URLs found in column '{url_column}'")
    return urls


def count_statuses(rows: list[dict], status_column: str = "mcat_status") -> StatusSummary:
    """Count statuses from result rows into standard summary buckets."""
    counts = Counter(r.get(status_column, "") for r in rows)
    return {
        "live": counts.get("Live", 0),
        # legacy "Removed" rows fold into unavailable (the status was retired)
        "unavailable": counts.get("Unavailable", 0) + counts.get("Removed", 0),
        "moderated": counts.get("Moderated", 0),
        "restricted": (
            counts.get("Restricted", 0)
            + counts.get("Age-restricted", 0)
            + counts.get("Geo-blocked", 0)
            + counts.get("Private", 0)
        ),
        "errors": counts.get("Error", 0),
        "unknown": counts.get("Unknown", 0),
        "login_required": counts.get("Login Required", 0),
    }


def validate_column_mapping(rows: list[dict], column_mapping: dict) -> tuple[bool, str]:
    """Validate that mapped columns exist."""
    if not rows:
        return False, "CSV is empty"
    columns = set(rows[0].keys())
    missing = [f"{k} column '{v}'" for k, v in column_mapping.items() if v and v not in columns]
    if missing:
        return False, f"Missing columns: {', '.join(missing)}"
    return True, ""


class IncrementalCSVWriter:
    """Thread-safe incremental CSV writer for real-time result saving."""

    def __init__(self, output_path: str, columns: list[str]):
        self.output_path: str = output_path
        self.columns: list[str] = columns
        self.lock: threading.Lock = threading.Lock()
        self.initialized: bool = False

    def write_header(self) -> None:
        with self.lock:
            output_dir = os.path.dirname(self.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
            self.initialized = True

    def append_row(self, row_data: dict[str, str]) -> None:
        if not self.initialized:
            raise Exception("Must call write_header() first")
        with self.lock:
            try:
                with open(self.output_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.columns)
                    writer.writerow(row_data)
            except Exception as e:
                print(f"Warning: Failed to write row to CSV: {e}")
