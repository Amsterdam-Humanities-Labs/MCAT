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
    removed: int
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


def empty_status_summary() -> StatusSummary:
    """A zero-filled summary, for use as a dataclass default before any rows
    have been counted."""
    return StatusSummary(
        live=0, removed=0, restricted=0, errors=0, unknown=0, login_required=0
    )
