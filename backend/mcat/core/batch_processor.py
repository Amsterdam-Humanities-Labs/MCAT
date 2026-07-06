import asyncio
import threading
from collections.abc import Callable
from queue import Queue
from pathlib import Path

from config.settings import config
from models.processing_models import ProcessingResult
from models.types import STATUS_BUCKETS, bucket_for
from utils.csv_handler import load_csv, get_columns, get_urls_from_column, validate_column_mapping, count_statuses, IncrementalCSVWriter
from core.browser_manager import BrowserSession
from scrapers.base_scraper import BaseScraper
from scrapers.youtube_scraper import YouTubeScraper
from scrapers.instagram_scraper import InstagramScraper
from scrapers.facebook_scraper import FacebookScraper
from scrapers.twitter_scraper import TwitterScraper


class BatchProcessor:
    """Async processing pipeline coordinator over a zendriver tab pool.

    process_csv_async runs inside an event loop spun up by the worker thread
    (asyncio.run). Concurrency is bounded by the BrowserSession tab pool, so the
    coroutines for all URLs are gathered but only pool_size run at once. Pause
    and cancel are plain threading.Events set from the worker/HTTP thread and
    polled between awaits.
    """

    def __init__(self, scraper_factory: Callable | None = None):
        self.cancel_flag: threading.Event = threading.Event()
        self.resume_event: threading.Event = threading.Event()
        self.resume_event.set()
        self.max_zendriver_tabs: int = config.scraper_settings['max_zendriver_tabs']
        self.log_callback: Callable | None = None
        self.progress_queue: Queue[dict] = Queue()
        self.progress_callback: Callable | None = None
        self._scraper_factory: Callable | None = scraper_factory
        # Set while a run's event loop is live, so cancel (from the HTTP thread)
        # can stop the browser and unblock in-flight tab calls immediately.
        self._loop: asyncio.AbstractEventLoop | None = None
        self._session: BrowserSession | None = None

    async def process_csv_async(self, csv_path: str, platform: str, column_mapping: dict[str, str],
                                output_folder: str | None = None, save_screenshots: bool = False,
                                cookies: list[dict] | None = None, auth_user: str = "anonymous") -> ProcessingResult:
        """Process a CSV file of URLs with incremental saving."""
        result = ProcessingResult()
        csv_writer = None
        output_csv_path = None
        scraper: BaseScraper | None = None
        session: BrowserSession | None = None

        try:
            self.cancel_flag.clear()
            self._loop = asyncio.get_running_loop()

            rows = load_csv(csv_path)
            columns = get_columns(rows)

            valid, error_msg = validate_column_mapping(rows, column_mapping)
            if not valid:
                result.error_message = error_msg
                return result

            if output_folder:
                output_csv_path = Path(output_folder) / "results.csv"
                url_col = column_mapping.get('post', columns[0])
                result_columns = ['mcat_status', 'mcat_detail', 'mcat_screenshot', 'mcat_timestamp', 'mcat_error', 'mcat_user']
                # mcat_index is a passthrough source column; surface it first.
                index_col = ['mcat_index'] if 'mcat_index' in columns else []
                other_columns = [c for c in columns if c != url_col and c not in result_columns and c != 'mcat_index']
                all_columns = [*index_col, url_col, *result_columns, *other_columns]
                csv_writer = IncrementalCSVWriter(
                    output_path=str(output_csv_path),
                    columns=all_columns
                )
                csv_writer.write_header()

            url_column = column_mapping.get('post', '')
            urls = get_urls_from_column(rows, url_column)
            self._log(f"Extracted {len(urls)} URLs from column '{url_column}'")

            if not urls:
                result.error_message = f"No URLs found in column '{url_column}'"
                return result

            # One browser + tab pool per run, torn down in finally (no leak class).
            if not self._scraper_factory:
                session = await BrowserSession.create(
                    pool_size=self.max_zendriver_tabs,
                    headless=config.scraper_settings['headless'],
                    log_callback=self.log_callback,
                    cookies=cookies or None,
                    platform=platform,
                )
                self._session = session

            scraper = self._create_scraper(platform, session)
            if not scraper:
                result.error_message = f"Unsupported platform: {platform}"
                return result

            if save_screenshots and output_folder:
                scraper.enable_screenshots(True, output_folder)

            self._log(f"Starting batch processing of {len(urls)} URLs...")
            await self._process_batch_async(urls, scraper, csv_writer, rows, url_column, auth_user)
            self._log(f"Batch processing completed", "success")

            if self.cancel_flag.is_set():
                result.error_message = "Processing was cancelled"
                if output_csv_path and output_csv_path.exists():
                    result.rows = load_csv(str(output_csv_path))
                return result

            if output_csv_path and output_csv_path.exists():
                result.rows = load_csv(str(output_csv_path))
            else:
                result.rows = rows

            if result.rows:
                result.stats = count_statuses(result.rows)
                result.processed_count = len(result.rows)

            result.success = True

        except Exception as e:
            result.error_message = str(e)

        finally:
            self._loop = None
            self._session = None
            if scraper is not None:
                scraper.cleanup()
            if session is not None:
                await session.stop()

        return result

    def _create_scraper(self, platform: str, session: BrowserSession | None) -> BaseScraper | None:
        """Create a scraper instance for the specified platform."""
        if self._scraper_factory:
            scraper = self._scraper_factory(platform)
            scraper.set_pause_event(self.resume_event)
            scraper.set_cancel_event(self.cancel_flag)
            return scraper

        assert session is not None
        scrapers: dict[str, type] = {
            'youtube': YouTubeScraper,
            'instagram': InstagramScraper,
            'facebook': FacebookScraper,
            'twitter': TwitterScraper,
        }
        cls = scrapers.get(platform)
        if not cls:
            return None

        scraper = cls(session, log_callback=self.log_callback)
        scraper.set_pause_event(self.resume_event)
        scraper.set_cancel_event(self.cancel_flag)
        return scraper

    def set_progress_callback(self, callback: Callable) -> None:
        self.progress_callback = callback

    def set_log_callback(self, callback: Callable) -> None:
        self.log_callback = callback

    def _log(self, message: str, level: str = "info") -> None:
        if self.log_callback:
            self.log_callback(message, level)

    async def _process_batch_async(self, urls: list[str], scraper: BaseScraper,
                                   csv_writer: IncrementalCSVWriter | None = None,
                                   original_rows: list[dict] | None = None,
                                   url_column: str | None = None,
                                   auth_user: str = "anonymous") -> None:
        """Process URLs concurrently (bounded by the tab pool) with incremental
        CSV writing. Single-threaded asyncio, so the stats/progress block runs
        with no await inside it and needs no lock."""
        processed = 0
        total = len(urls)
        stats = {bucket: 0 for bucket in STATUS_BUCKETS}
        original_rows = original_rows or []

        async def process_single_url(url: str, row_index: int) -> None:
            nonlocal processed
            if self.cancel_flag.is_set():
                return

            try:
                result = await scraper.check_url_status(url)

                if self.cancel_flag.is_set() or result.status.lower() == 'cancelled':
                    return

                if csv_writer and original_rows:
                    original_row = original_rows[row_index].copy()
                    original_row.update({
                        'mcat_status': result.status,
                        'mcat_detail': result.info,
                        'mcat_screenshot': result.screenshot_path or '',
                        'mcat_timestamp': result.timestamp,
                        'mcat_error': result.error_message,
                        'mcat_user': auth_user,
                    })
                    csv_writer.append_row(original_row)

                stats[bucket_for(result.status)] += 1

                processed += 1
                current_processed = processed
                current_stats = stats.copy()

                self._log(f"[{current_processed}/{total}] {url} → {result.status}", "info")

                if self.cancel_flag.is_set():
                    return

                current_action = f"Checking: {url[:60]}{'...' if len(url) > 60 else ''}"
                if self.progress_callback:
                    self.progress_callback(current_stats, total, current_processed, current_action)
                else:
                    self.progress_queue.put({
                        'current': current_processed,
                        'total': total,
                        'stats': current_stats,
                        'current_action': current_action
                    })

            except Exception as e:
                if not self.cancel_flag.is_set():
                    self._log(f"Error processing URL {url}: {e}", "error")
                stats['errors'] += 1
                processed += 1

        await asyncio.gather(*(process_single_url(url, idx) for idx, url in enumerate(urls)))

    def pause_processing(self) -> None:
        self.resume_event.clear()

    def resume_processing(self) -> None:
        self.resume_event.set()

    def cancel_processing(self) -> None:
        self.cancel_flag.set()
        self.resume_event.set()
        # Stop the browser from the worker's loop (this is usually called from the
        # HTTP thread). In-flight tab/CDP calls then fail at once and the batch
        # unwinds immediately, instead of waiting out the per-op timeouts.
        loop, session = self._loop, self._session
        if loop is not None and session is not None:
            try:
                loop.call_soon_threadsafe(lambda: loop.create_task(session.stop()))
            except Exception:
                pass

    def cleanup(self) -> None:
        # The per-run BrowserSession is stopped in process_csv_async's finally;
        # here we just signal cancellation so an in-flight batch winds down.
        self.cancel_flag.set()
