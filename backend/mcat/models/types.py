"""Shared structural types for dict-shaped data that has a fixed schema.

Domain entities are dataclasses (the rest of `models/`). These TypedDicts cover
the transient, JSON-friendly dicts that flow between the CSV layer, the run
service, and the API but still have a known, stable set of keys — so a typo in
a key is a type error instead of a silently-wrong count.

Genuinely dynamic dicts are intentionally NOT modelled here: CSV rows
(`list[dict]`, columns are user data), browser cookie dicts (external shape),
and `changes_summary` (keys like ``live_to_removed`` are derived at runtime).
"""
from __future__ import annotations

from typing import TypedDict


class StatusSummary(TypedDict):
    """Counts of result rows per status bucket, as produced by
    `utils.csv_handler.count_statuses`. The key set is fixed and the values
    sum to the run's ``total_checked``."""
    live: int
    unavailable: int
    moderated: int
    restricted: int
    errors: int
    unknown: int
    login_required: int


class StatusChange(TypedDict):
    """One URL whose status differs from the previous run. Mirrors a row of
    ``changes.csv``."""
    url: str
    previous_status: str
    new_status: str


# Raw mcat_status strings that fold into each summary bucket (matched
# case-insensitively), including legacy values the taxonomy collapsed. This is
# the single source for the string->bucket mapping; count_statuses, the batch
# tally, and the SSE payload all go through bucket_for / the keys here.
STATUS_BUCKETS: dict[str, tuple[str, ...]] = {
    "live": ("Live",),
    "unavailable": ("Unavailable", "Removed"),
    "moderated": ("Moderated",),
    "restricted": ("Restricted", "Age-restricted", "Geo-blocked", "Private"),
    "login_required": ("Login Required",),
    "unknown": ("Unknown",),
    "errors": ("Error",),
}

# Fails at import if the buckets and the StatusSummary schema ever drift apart.
assert set(STATUS_BUCKETS) == set(StatusSummary.__annotations__)

_BUCKET_BY_STATUS = {raw.lower(): bucket for bucket, raws in STATUS_BUCKETS.items() for raw in raws}


def bucket_for(status: str) -> str:
    """Summary bucket for a raw mcat_status (case-insensitive). Anything
    unrecognized falls to ``errors`` so the buckets always sum to the row count."""
    return _BUCKET_BY_STATUS.get((status or "").strip().lower(), "errors")


def empty_status_summary() -> StatusSummary:
    """A zero-filled summary, for use as a dataclass default before any rows
    have been counted."""
    return StatusSummary(**{bucket: 0 for bucket in STATUS_BUCKETS})
