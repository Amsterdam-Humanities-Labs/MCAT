import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from pathlib import Path

from config.settings import config
from models.processing_models import ProcessingResult
from utils.csv_handler import load_csv, get_columns, get_urls_from_column, validate_column_mapping, count_statuses, IncrementalCSVWriter
from core.driver_manager import WebDriverPool
from scrapers.base_scraper import BaseScraper
from scrapers.youtube_scraper import YouTubeScraper
from scrapers.instagram_scraper import InstagramScraper
from scrapers.facebook_scraper import FacebookScraper
from scrapers.twitter_scraper import TwitterScraper


class BatchProcessor:
    """Main processing pipeline coordinator with WebDriver pooling."""

    def __init__(self, scraper_factory: Callable | None = None):
        self.cancel_flag: threading.Event = threading.Event()
        self.resume_event: threading.Event = threading.Event()
        self.resume_event.set()
        self.max_workers: int = config.scraper_settings['max_workers']
        self.log_callback: Callable | None = None
        self.driver_pool: WebDriverPool | None = None
        self.progress_queue: Queue[dict] = Queue()
        self.progress_callback: Callable | None = None
        self._scraper_factory: Callable | None = scraper_factory

    def process_csv(self, csv_path: str, platform: str, column_mapping: dict[str, str],
                   output_folder: str | None = None, save_screenshots: bool = False,
                   cookies: list[dict] | None = None, auth_user: str = "anonymous") -> ProcessingResult:
        """Process a CSV file of URLs with incremental saving."""
        result = ProcessingResult()
        csv_writer = None
        output_csv_path = None
        scraper: BaseScraper | None = None

        if self.driver_pool is None and not self._scraper_factory:
            self.driver_pool = WebDriverPool(
                pool_size=self.max_workers,
                headless=config.scraper_settings['headless'],
                log_callback=self.log_callback,
                cookies=cookies or None,
                platform=platform,
            )

        try:
            self.cancel_flag.clear()

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
                other_columns = [c for c in columns if c != url_col and c not in result_columns]
                all_columns = [url_col, *result_columns, *other_columns]
                csv_writer = IncrementalCSVWriter(
                    output_path=str(output_csv_path),
                    columns=all_columns
                )
                csv_writer.write_header()

            scraper = self._create_scraper(platform)
            if not scraper:
                result.error_message = f"Unsupported platform: {platform}"
                return result

            if save_screenshots and output_folder:
                scraper.enable_screenshots(True, output_folder)

            url_column = column_mapping.get('post', '')
            urls = get_urls_from_column(rows, url_column)
            self._log(f"Extracted {len(urls)} URLs from column '{url_column}'")

            if not urls:
                result.error_message = f"No URLs found in column '{url_column}'"
                return result

            self._log(f"Starting batch processing of {len(urls)} URLs...")
            self._process_batch(urls, scraper, csv_writer, rows, url_column, auth_user)
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
            if scraper is not None:
                scraper.cleanup()
            self.cleanup()

        return result

    def _create_scraper(self, platform: str) -> BaseScraper | None:
        """Create a scraper instance for the specified platform."""
        if self._scraper_factory:
            scraper = self._scraper_factory(platform)
            scraper.set_pause_event(self.resume_event)
            scraper.set_cancel_event(self.cancel_flag)
            return scraper

        assert self.driver_pool is not None
        scrapers: dict[str, type] = {
            'youtube': YouTubeScraper,
            'instagram': InstagramScraper,
            'facebook': FacebookScraper,
            'twitter': TwitterScraper,
        }
        cls = scrapers.get(platform)
        if not cls:
            return None

        scraper = cls(self.driver_pool, log_callback=self.log_callback)
        scraper.set_pause_event(self.resume_event)
        scraper.set_cancel_event(self.cancel_flag)
        return scraper

    def set_progress_callback(self, callback: Callable) -> None:
        self.progress_callback = callback

    def set_log_callback(self, callback: Callable) -> None:
        self.log_callback = callback

    def _log(self, message: str, level: str = "info") -> None:
        if hasattr(self, 'log_callback') and self.log_callback:
            self.log_callback(message, level)

    def _process_batch(self, urls: list[str], scraper: BaseScraper,
                      csv_writer: IncrementalCSVWriter | None = None,
                      original_rows: list[dict] | None = None,
                      url_column: str | None = None,
                      auth_user: str = "anonymous") -> None:
        """Process URLs in parallel batches with incremental CSV writing."""
        processed = 0
        total = len(urls)

        stats_lock = threading.Lock()
        stats = {'live': 0, 'removed': 0, 'restricted': 0, 'errors': 0, 'unknown': 0, 'login_required': 0, 'skipped': 0}

        original_rows = original_rows or []

        def process_single_url(url: str, row_index: int) -> None:
            nonlocal processed
            if self.cancel_flag.is_set():
                return

            try:
                result = scraper.check_url_status(url)

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

                with stats_lock:
                    status = result.status.lower()
                    if status == 'live':
                        stats['live'] += 1
                    elif status == 'removed':
                        stats['removed'] += 1
                    elif status in ['restricted', 'age-restricted', 'geo-blocked', 'private']:
                        stats['restricted'] += 1
                    elif status == 'unknown':
                        stats['unknown'] += 1
                    elif status == 'login required':
                        stats['login_required'] += 1
                    else:
                        stats['errors'] += 1

                    processed += 1
                    current_processed = processed
                    current_stats = stats.copy()

                short_url = url[:50] + '...' if len(url) > 50 else url
                self._log(f"[{current_processed}/{total}] {short_url} → {result.status}", "info")

                if self.cancel_flag.is_set():
                    return

                current_action = f"Checking: {url[:60]}{'...' if len(url) > 60 else ''}"
                if self.progress_callback:
                    self.progress_callback(current_stats, total, current_processed, current_action)
                else:
                    progress_data = {
                        'current': current_processed,
                        'total': total,
                        'stats': current_stats,
                        'current_action': current_action
                    }
                    self.progress_queue.put(progress_data)

            except Exception as e:
                if not self.cancel_flag.is_set():
                    self._log(f"Error processing URL {url}: {e}", "error")
                with stats_lock:
                    stats['errors'] += 1
                    processed += 1

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for idx, url in enumerate(urls):
                if self.cancel_flag.is_set():
                    break
                futures.append(executor.submit(process_single_url, url, idx))

            cancelled = False
            for future in as_completed(futures):
                if self.cancel_flag.is_set() and not cancelled:
                    cancelled = True
                    self._log("Cancellation requested - stopping workers...", "info")
                    for f in futures:
                        f.cancel()
                if cancelled:
                    continue
                try:
                    future.result()
                except Exception as e:
                    if not self.cancel_flag.is_set():
                        self._log(f"Error in future result: {e}", "error")

    def pause_processing(self) -> None:
        self.resume_event.clear()

    def resume_processing(self) -> None:
        self.resume_event.set()

    def cancel_processing(self) -> None:
        self.cancel_flag.set()
        self.resume_event.set()

    def cleanup(self) -> None:
        self.cancel_flag.set()
        if hasattr(self, 'driver_pool') and self.driver_pool:
            self.driver_pool.cleanup()
            self.driver_pool = None
