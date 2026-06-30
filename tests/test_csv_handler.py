"""Unit tests for utils.csv_handler — the input/output data layer."""
import pytest

from utils.csv_handler import (
    load_csv,
    get_columns,
    normalize_url,
    get_urls_from_column,
    count_statuses,
    assign_url_indices,
    validate_column_mapping,
    IncrementalCSVWriter,
)


def _write(path, content):
    path.write_text(content, encoding="utf-8")
    return str(path)


# --- load_csv ---

def test_load_csv_comma(tmp_path):
    rows = load_csv(_write(tmp_path / "c.csv", "url,title\nhttp://a,A\nhttp://b,B\n"))
    assert rows == [{"url": "http://a", "title": "A"}, {"url": "http://b", "title": "B"}]


def test_load_csv_single_column(tmp_path):
    rows = load_csv(_write(tmp_path / "s.csv", "url\nhttp://a\nhttp://b\n"))
    assert [r["url"] for r in rows] == ["http://a", "http://b"]


def test_load_csv_strips_bom(tmp_path):
    # Excel writes a UTF-8 BOM; the header must not become "﻿url".
    rows = load_csv(_write(tmp_path / "b.csv", "﻿url,title\nhttp://a,A\n"))
    assert list(rows[0].keys()) == ["url", "title"]


def test_load_csv_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_csv(str(tmp_path / "nope.csv"))


def test_load_csv_semicolon(tmp_path):
    rows = load_csv(_write(tmp_path / "sc.csv", "url;title\nhttp://a;A\n"))
    assert rows == [{"url": "http://a", "title": "A"}]


def test_load_csv_tab(tmp_path):
    rows = load_csv(_write(tmp_path / "t.csv", "url\ttitle\nhttp://a\tA\n"))
    assert rows == [{"url": "http://a", "title": "A"}]


# --- get_columns ---

def test_get_columns():
    assert get_columns([{"a": "1", "b": "2"}]) == ["a", "b"]
    assert get_columns([]) == []


# --- normalize_url ---

@pytest.mark.parametrize("raw,expected", [
    ("http://a.com", "http://a.com"),
    ("https://a.com", "https://a.com"),
    ("a.com", "https://a.com"),
    ("  a.com  ", "https://a.com"),
    ("", ""),
])
def test_normalize_url(raw, expected):
    assert normalize_url(raw) == expected


# --- get_urls_from_column ---

def test_get_urls_skips_blanks_and_normalizes():
    rows = [{"u": "a.com"}, {"u": ""}, {"u": "http://b.com"}, {}]
    assert get_urls_from_column(rows, "u") == ["https://a.com", "http://b.com"]


def test_get_urls_empty_raises():
    with pytest.raises(ValueError):
        get_urls_from_column([{"u": ""}, {"u": ""}], "u")


# --- count_statuses ---

def test_count_statuses_buckets():
    rows = [{"mcat_status": s} for s in [
        "Live", "Live", "Unavailable", "Removed",  # legacy "Removed" folds into unavailable
        "Moderated",
        "Restricted", "Age-restricted", "Geo-blocked", "Private",  # all -> restricted
        "Login Required", "Unknown", "Error",
    ]]
    counts = count_statuses(rows)
    assert counts["live"] == 2
    assert counts["unavailable"] == 2         # Unavailable + legacy Removed
    assert counts["moderated"] == 1
    assert counts["restricted"] == 4          # Restricted + Age-restricted + Geo-blocked + Private
    assert counts["login_required"] == 1
    assert counts["unknown"] == 1
    assert counts["errors"] == 1


# --- assign_url_indices ---

def test_assign_url_indices_fresh_is_1_based():
    rows = [{"url": "a"}, {"url": "b"}, {"url": "c"}]
    out, nxt = assign_url_indices(rows, 1)
    assert [r["mcat_index"] for r in out] == ["1", "2", "3"]
    assert nxt == 4


def test_assign_url_indices_fills_only_missing_from_counter():
    # Two existing rows keep their numbers; the new/blank rows draw from the
    # counter (which has already advanced past the originals).
    rows = [{"url": "a", "mcat_index": "1"}, {"url": "b"}, {"url": "c", "mcat_index": ""}]
    out, nxt = assign_url_indices(rows, 3)
    assert [r["mcat_index"] for r in out] == ["1", "3", "4"]
    assert nxt == 5


def test_assign_url_indices_idempotent():
    rows = [{"url": "a"}, {"url": "b"}]
    rows, nxt = assign_url_indices(rows, 1)
    rows, nxt2 = assign_url_indices(rows, nxt)  # nothing left to assign
    assert nxt2 == nxt == 3
    assert [r["mcat_index"] for r in rows] == ["1", "2"]


# --- validate_column_mapping ---

def test_validate_mapping_empty_rows():
    ok, msg = validate_column_mapping([], {"post": "url"})
    assert ok is False and "empty" in msg.lower()


def test_validate_mapping_missing_column():
    ok, msg = validate_column_mapping([{"url": "x"}], {"post": "link"})
    assert ok is False and "Missing columns" in msg


def test_validate_mapping_ok():
    ok, msg = validate_column_mapping([{"url": "x"}], {"post": "url"})
    assert ok is True and msg == ""


# --- IncrementalCSVWriter ---

def test_incremental_writer_header_and_append(tmp_path):
    out = tmp_path / "out.csv"
    w = IncrementalCSVWriter(str(out), ["url", "mcat_status"])
    w.write_header()
    w.append_row({"url": "http://a", "mcat_status": "Live"})
    w.append_row({"url": "http://b", "mcat_status": "Removed"})
    rows = load_csv(str(out))
    assert rows == [
        {"url": "http://a", "mcat_status": "Live"},
        {"url": "http://b", "mcat_status": "Removed"},
    ]


def test_incremental_writer_append_before_header_raises(tmp_path):
    w = IncrementalCSVWriter(str(tmp_path / "out.csv"), ["url"])
    with pytest.raises(Exception):
        w.append_row({"url": "http://a"})
