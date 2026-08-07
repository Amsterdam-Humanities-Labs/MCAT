"""Worker-level tests for ProcessingService's subset selection.

The tracking path hands start_processing a list of *normalized* URLs, while the
rows it filters come straight from urls.csv. These cover that boundary; the
worker is driven directly (no thread) with an injected scripted scraper.
"""
import pytest

from core.batch_processor import BatchProcessor
from models.file_models import FileInfo, ColumnMapping
from models.processing_models import ProcessingJob, ProcessingState
from services.processing_service import ProcessingService
from utils.csv_handler import load_csv

from test_batch_processor import ScriptedScraper


def _job(tmp_path, rows, url_column="url"):
    file_info = FileInfo(path=str(tmp_path / "urls.csv"))
    file_info.rows = rows
    file_info.row_count = len(rows)
    file_info.columns = list(rows[0].keys()) if rows else []
    file_info.valid = True

    mapping = ColumnMapping()
    mapping.post_column = url_column

    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    return ProcessingJob(
        file_info=file_info,
        column_mapping=mapping,
        platform="test",
        output_folder=str(out),
    )


def _service(scraper, urls):
    svc = ProcessingService(platform="test")
    svc._batch_processor = BatchProcessor(scraper_factory=lambda platform: scraper)
    svc._custom_urls = urls
    return svc


def _started(tmp_path, scraper, rows=None):
    """Drive the real start_processing path (spawns the worker thread)."""
    rows = rows or [{"url": "http://a"}, {"url": "http://b"}]
    svc = ProcessingService(platform="test", scraper_factory=lambda platform: scraper)
    assert svc.start_processing(_job(tmp_path, rows)) is True
    return svc


def test_worker_is_a_daemon_and_join_waits_for_it(tmp_path):
    """Shutdown needs a bounded join; the daemon flag is the backstop if it times out."""
    svc = _started(tmp_path, ScriptedScraper(default="Live"))

    assert svc._processing_thread.daemon is True
    assert svc.join(timeout=10) is True
    assert not svc._processing_thread.is_alive()
    assert svc.is_idle()


def test_join_returns_true_when_no_worker_ran(tmp_path):
    assert ProcessingService(platform="test").join(timeout=0.1) is True


def test_cleanup_goes_through_cancel_processing(tmp_path):
    """Setting cancel_flag alone leaves the browser running out its page-load
    timeout; only cancel_processing stops it from the worker's loop. Asserting
    the delegation, since with an injected scraper there is no browser to observe."""
    svc = _started(tmp_path, ScriptedScraper(default="Live", delay=0.05))
    batch = svc._batch_processor
    calls = []
    batch.cancel_processing = lambda: calls.append("cancel_processing")

    svc.cleanup()

    assert calls == ["cancel_processing"]
    svc.join(timeout=10)


def test_second_start_is_refused_while_a_run_is_active(tmp_path):
    svc = _started(tmp_path, ScriptedScraper(default="Live", delay=0.05))

    assert svc.start_processing(_job(tmp_path, [{"url": "http://c"}])) is False
    assert "already in progress" in svc.last_start_error
    svc.join(timeout=10)


def test_scheme_less_rows_match_the_normalized_selection(tmp_path):
    """urls.csv holds bare and padded cells; the selection holds normalized URLs."""
    rows = [
        {"url": "youtube.com/watch?v=a"},
        {"url": " https://youtube.com/watch?v=b "},
        {"url": "https://youtube.com/watch?v=c"},
    ]
    job = _job(tmp_path, rows)
    selection = ["https://youtube.com/watch?v=a", "https://youtube.com/watch?v=b"]

    svc = _service(ScriptedScraper(default="Live"), selection)
    svc._processing_worker(job)

    written = load_csv(str(tmp_path / "out" / "results.csv"))
    assert {r["url"] for r in written} == {rows[0]["url"], rows[1]["url"]}
    assert svc.current_status.state is not ProcessingState.ERROR


def test_selection_matching_no_rows_reports_a_usable_error(tmp_path):
    """A zero-match selection must name the problem, not fail later on a temp path."""
    job = _job(tmp_path, [{"url": "https://youtube.com/watch?v=a"}])

    svc = _service(ScriptedScraper(), ["https://youtube.com/watch?v=missing"])
    svc._processing_worker(job)

    assert svc.current_status.state is ProcessingState.ERROR
    message = svc.current_status.error_message
    assert "selected URLs matched" in message
    assert "url" in message
