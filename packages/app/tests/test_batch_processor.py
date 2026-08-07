"""Batch-orchestration tests for BatchProcessor (no browser — injected fake scraper).

Exercises the concurrent pipeline, incremental CSV, stats, and pause/cancel via the
`_scraper_factory` seam, with a scripted scraper that overrides check_url_status.
"""
import asyncio
import pytest

from core.batch_processor import BatchProcessor
from scrapers.base_scraper import BaseScraper, ScrapingResult
from utils.csv_handler import load_csv


class ScriptedScraper(BaseScraper):
    def __init__(self, status_map=None, default="Live", delay=0.0):
        super().__init__(session=None)
        self.status_map = status_map or {}
        self.default = default
        self.delay = delay
        self.seen = []

    def get_platform_name(self):
        return "test"

    async def check_url_status(self, url):
        self.seen.append(url)
        if self.is_cancelled():
            return ScrapingResult(url=url, status="Cancelled", info="cancelled")
        await self._check_pause()
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.is_cancelled():
            return ScrapingResult(url=url, status="Cancelled", info="cancelled")
        return ScrapingResult(url=url, status=self.status_map.get(url, self.default))


def _csv(tmp_path, urls):
    p = tmp_path / "in.csv"
    p.write_text("url\n" + "\n".join(urls) + "\n", encoding="utf-8")
    return str(p)


def _csv_rows(tmp_path, rows, columns=("url", "note")):
    """CSV from explicit rows, so a blank URL cell still yields a parsed row.

    The single-column helper cannot express this: a blank there is an empty
    line, which DictReader skips.
    """
    p = tmp_path / "in.csv"
    lines = [",".join(columns)]
    lines += [",".join(r.get(c, "") for c in columns) for r in rows]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def _proc(scraper):
    return BatchProcessor(scraper_factory=lambda platform: scraper)


def _results(out):
    f = out / "results.csv"
    return load_csv(str(f)) if f.exists() else []


async def test_happy_path(tmp_path):
    urls = ["http://a", "http://b", "http://c"]
    out = tmp_path / "out"; out.mkdir()
    result = await _proc(ScriptedScraper(default="Live")).process_csv_async(
        _csv(tmp_path, urls), "test", {"post": "url"}, output_folder=str(out))
    assert result.success
    rows = _results(out)
    assert len(rows) == 3 and all(r["mcat_status"] == "Live" for r in rows)
    assert result.stats["live"] == 3


async def test_mixed_statuses_bucket_into_stats(tmp_path):
    smap = {"http://a": "Live", "http://b": "Unavailable",
            "http://c": "Private", "http://d": "Unknown", "http://e": "Moderated"}
    out = tmp_path / "out"; out.mkdir()
    result = await _proc(ScriptedScraper(status_map=smap)).process_csv_async(
        _csv(tmp_path, list(smap)), "test", {"post": "url"}, output_folder=str(out))
    assert result.success
    assert result.stats["live"] == 1
    assert result.stats["unavailable"] == 1
    assert result.stats["moderated"] == 1
    assert result.stats["restricted"] == 1     # Private collapses into restricted
    assert result.stats["unknown"] == 1


async def test_cancel_stops_mid_run(tmp_path):
    urls = [f"http://{i}" for i in range(5)]
    out = tmp_path / "out"; out.mkdir()
    proc = _proc(ScriptedScraper(delay=0.2))
    task = asyncio.create_task(proc.process_csv_async(
        _csv(tmp_path, urls), "test", {"post": "url"}, output_folder=str(out)))
    await asyncio.sleep(0.02)
    proc.cancel_processing()
    result = await task
    assert "cancelled" in result.error_message.lower()
    assert len(_results(out)) < len(urls)


async def test_pause_holds_then_resume_completes(tmp_path):
    urls = ["http://a", "http://b"]
    out = tmp_path / "out"; out.mkdir()
    proc = _proc(ScriptedScraper())
    proc.pause_processing()
    task = asyncio.create_task(proc.process_csv_async(
        _csv(tmp_path, urls), "test", {"post": "url"}, output_folder=str(out)))
    await asyncio.sleep(0.1)
    assert not task.done()                      # blocked by pause
    proc.resume_processing()
    result = await task
    assert result.success and len(_results(out)) == 2


async def test_blank_url_cell_keeps_results_on_their_own_rows(tmp_path):
    """A blank URL cell must not shift later results onto the wrong row.

    Asserts per-row correspondence rather than aggregate counts: the bug leaves
    the totals correct while pairing each status with the wrong url.
    """
    rows = [
        {"url": "http://a", "note": "first"},
        {"url": "", "note": "orphan"},
        {"url": "http://c", "note": "third"},
        {"url": "http://d", "note": "fourth"},
    ]
    smap = {"http://a": "Live", "http://c": "Unavailable", "http://d": "Moderated"}
    out = tmp_path / "out"; out.mkdir()

    result = await _proc(ScriptedScraper(status_map=smap)).process_csv_async(
        _csv_rows(tmp_path, rows), "test", {"post": "url"}, output_folder=str(out))

    assert result.success
    written = _results(out)
    assert len(written) == 3
    for r in written:
        assert r["mcat_status"] == smap[r["url"]]
    assert "orphan" not in [r.get("note") for r in written]


async def test_bad_column_mapping_fails(tmp_path):
    out = tmp_path / "out"; out.mkdir()
    result = await _proc(ScriptedScraper()).process_csv_async(
        _csv(tmp_path, ["http://a"]), "test", {"post": "nope"}, output_folder=str(out))
    assert result.success is False
    assert "missing" in result.error_message.lower()
