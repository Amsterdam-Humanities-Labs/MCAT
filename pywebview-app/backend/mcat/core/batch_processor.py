import polars as pl
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable
from queue import Queue
from pathlib import Path

from config.settings import config
from utils.csv_handler import CSVHandler, IncrementalCSVWriter
from core.driver_manager import WebDriverPool
from scrapers.youtube_scraper import YouTubeScraper
from scrapers.instagram_scraper import InstagramScraper
from scrapers.facebook_scraper import FacebookScraper
from scrapers.twitter_scraper import TwitterScraper


class ProcessingResult:
    """Result container for batch processing operations."""

    def __init__(self):
        self.success: bool = False
        self.dataframe: Optional[pl.DataFrame] = None
        self.error_message: str = ""
        self.processed_count: int = 0
        self.stats: Dict[str, int] = {
            'live': 0,
            'removed': 0,
            'restricted': 0,
            'errors': 0
        }


class BatchProcessor:
    """Main processing pipeline coordinator with WebDriver pooling."""

    def __init__(self):
        # Removed state_manager dependency - now handled by ProcessingCoordinator
        self.cancel_flag = threading.Event()
        # For pause: Event that is SET when NOT paused (inverse logic for efficiency)
        self.resume_event = threading.Event()
        self.resume_event.set()  # Start in resumed state
        self.max_workers = config.scraper_settings['max_workers']
        self.log_callback = None

        # WebDriver pool initialized lazily when log_callback is set
        self.driver_pool = None

        # Thread-safe progress queue for GUI updates
        self.progress_queue = Queue()
        self.progress_callback = None

    def process_csv(self, csv_path: str, platform: str, column_mapping: Dict[str, str],
                   output_folder: str = None, save_screenshots: bool = False) -> ProcessingResult:
        """Process a CSV file of URLs with incremental saving."""
        result = ProcessingResult()
        csv_writer = None
        output_csv_path = None

        # Ensure driver pool is initialized (skip for mock mode)
        import os
        if self.driver_pool is None and not os.environ.get("MCAT_MOCK"):
            self.driver_pool = WebDriverPool(
                pool_size=self.max_workers,
                headless=config.scraper_settings['headless'],
                log_callback=self.log_callback
            )

        try:
            # Reset cancel flag
            self.cancel_flag.clear()

            # Step 1: Load CSV
            df = CSVHandler.load_csv(csv_path)

            # Step 2: Validate data
            valid, error_msg = CSVHandler.validate_column_mapping(df, column_mapping)
            if not valid:
                result.error_message = error_msg
                return result

            # Step 3: Setup incremental CSV writer if output folder provided
            if output_folder:
                output_csv_path = Path(output_folder) / "results.csv"
                # Include all original columns plus result columns
                result_columns = ['status', 'info', 'screenshot_path', 'timestamp', 'error_message', 'platform']
                all_columns = list(df.columns) + result_columns
                csv_writer = IncrementalCSVWriter(
                    output_path=str(output_csv_path),
                    columns=all_columns
                )
                csv_writer.write_header()

            # Step 4: Initialize scraper
            scraper = self._create_scraper(platform)
            if not scraper:
                result.error_message = f"Unsupported platform: {platform}"
                return result

            # Enable screenshots if requested
            if save_screenshots and output_folder:
                scraper.enable_screenshots(True, output_folder)

            # Step 5: Extract URLs
            url_column = column_mapping.get('post', '')
            urls = CSVHandler.get_urls_from_column(df, url_column)
            self._log(f"Extracted {len(urls)} URLs from column '{url_column}'")

            if not urls:
                result.error_message = f"No URLs found in column '{url_column}'"
                return result

            # Step 6: Process URLs with incremental writing
            self._log(f"Starting batch processing of {len(urls)} URLs...")
            self._process_batch(urls, scraper, csv_writer, df, url_column)
            self._log(f"Batch processing completed", "success")

            if self.cancel_flag.is_set():
                result.error_message = "Processing was cancelled"
                # Still load partial results from CSV if available
                if output_csv_path and output_csv_path.exists():
                    result.dataframe = pl.read_csv(output_csv_path)
                return result

            # Step 7: Load CSV back into memory for GUI table
            if output_csv_path and output_csv_path.exists():
                result.dataframe = pl.read_csv(output_csv_path)
            else:
                # Fallback if no CSV was saved (shouldn't happen)
                result.dataframe = df

            # Calculate final stats from loaded DataFrame
            if result.dataframe is not None:
                status_counts = result.dataframe.group_by('status').len().to_dicts()
                counts_dict = {row['status']: row['len'] for row in status_counts}
                result.stats = {
                    'live': counts_dict.get('Live', 0),
                    'removed': counts_dict.get('Removed', 0),
                    'restricted': counts_dict.get('Restricted', 0) + counts_dict.get('Age-restricted', 0) +
                                  counts_dict.get('Geo-blocked', 0) + counts_dict.get('Private', 0),
                    'errors': counts_dict.get('Error', 0)
                }
                result.processed_count = len(result.dataframe)

            result.success = True

        except Exception as e:
            result.error_message = str(e)

        finally:
            # Cleanup scraper and WebDriver pool
            if 'scraper' in locals():
                scraper.cleanup()

            # Always cleanup WebDriver pool to close Chrome browsers
            self.cleanup()

        return result

    def _create_scraper(self, platform: str):
        """Create a scraper instance for the specified platform."""
        import os
        if os.environ.get("MCAT_MOCK"):
            import sys
            tests_dir = str(Path(__file__).parent.parent.parent.parent / "tests")
            if tests_dir not in sys.path:
                sys.path.insert(0, tests_dir)
            from mock_scraper import MockScraper
            scraper = MockScraper()
            scraper.set_pause_event(self.resume_event)
            scraper.set_cancel_event(self.cancel_flag)
            self._log("Using mock scraper (MCAT_MOCK=1)", "info")
            return scraper

        if platform == 'youtube':
            scraper = YouTubeScraper(self.driver_pool)
            scraper.set_pause_event(self.resume_event)
            scraper.set_cancel_event(self.cancel_flag)
            return scraper
        elif platform == 'instagram':
            scraper = InstagramScraper(self.driver_pool)
            scraper.set_pause_event(self.resume_event)
            scraper.set_cancel_event(self.cancel_flag)
            return scraper
        elif platform == 'facebook':
            scraper = FacebookScraper(self.driver_pool)
            scraper.set_pause_event(self.resume_event)
            scraper.set_cancel_event(self.cancel_flag)
            return scraper
        elif platform == 'twitter':
            scraper = TwitterScraper(self.driver_pool)
            scraper.set_pause_event(self.resume_event)
            scraper.set_cancel_event(self.cancel_flag)
            return scraper
        return None

    def set_progress_callback(self, callback):
        """Set callback function for progress updates."""
        self.progress_callback = callback

    def set_log_callback(self, callback):
        """Set callback function for log messages."""
        self.log_callback = callback
        # Initialize driver pool with log callback
        if self.driver_pool is None:
            self.driver_pool = WebDriverPool(
                pool_size=self.max_workers,
                headless=config.scraper_settings['headless'],
                log_callback=callback
            )

    def _log(self, message: str, level: str = "info"):
        """Send log message via callback if available."""
        if hasattr(self, 'log_callback') and self.log_callback:
            self.log_callback(message, level)

    def _process_batch(self, urls: List[str], scraper,
                      csv_writer: Optional[IncrementalCSVWriter] = None,
                      original_df: Optional[pl.DataFrame] = None,
                      url_column: str = None) -> None:
        """Process URLs in parallel batches with incremental CSV writing."""
        processed = 0
        total = len(urls)

        # Thread-safe counters
        stats_lock = threading.Lock()
        stats = {'live': 0, 'removed': 0, 'restricted': 0, 'errors': 0, 'skipped': 0}

        # Convert dataframe to list of dicts for easier row access
        original_rows = original_df.to_dicts() if original_df is not None else []

        def process_single_url(url: str, row_index: int) -> None:
            nonlocal processed
            if self.cancel_flag.is_set():
                return

            try:
                # Check URL using shared scraper
                result = scraper.check_url_status(url)

                # Don't process results after cancellation - just exit silently
                if self.cancel_flag.is_set() or result.status.lower() == 'cancelled':
                    return

                # Write to CSV incrementally if writer provided
                if csv_writer and original_rows:
                    # Get original row data
                    original_row = original_rows[row_index].copy()
                    # Add scraping results
                    original_row.update({
                        'status': result.status,
                        'info': result.info,
                        'screenshot_path': result.screenshot_path or '',
                        'timestamp': result.timestamp,
                        'error_message': result.error_message,
                        'platform': result.platform
                    })
                    csv_writer.append_row(original_row)

                # Thread-safe stats update
                with stats_lock:
                    status = result.status.lower()
                    if status == 'live':
                        stats['live'] += 1
                    elif status == 'removed':
                        stats['removed'] += 1
                    elif status in ['restricted', 'age-restricted', 'geo-blocked', 'private']:
                        stats['restricted'] += 1
                    else:
                        stats['errors'] += 1

                    processed += 1
                    current_processed = processed
                    current_stats = stats.copy()

                # Log the result
                short_url = url[:50] + '...' if len(url) > 50 else url
                log_level = "success" if status == "live" else "info" if status in ["removed", "restricted", "private"] else "error"
                self._log(f"[{current_processed}/{total}] {short_url} → {result.status}", log_level)

                # Don't send progress updates after cancellation
                if self.cancel_flag.is_set():
                    return

                # Send progress update via callback or queue
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

        # Process URLs with threading - submit in batches for better cancellation
        self._log(f"Starting ThreadPoolExecutor with {self.max_workers} workers for {len(urls)} URLs", "debug")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            # Submit all tasks
            for idx, url in enumerate(urls):
                if self.cancel_flag.is_set():
                    break
                futures.append(executor.submit(process_single_url, url, idx))

            self._log(f"Submitted {len(futures)} tasks to executor", "debug")

            # Wait for completion, handling cancellation
            cancelled = False
            for future in as_completed(futures):
                if self.cancel_flag.is_set() and not cancelled:
                    cancelled = True
                    self._log("Cancellation requested - stopping workers...", "info")
                    # Cancel all pending futures
                    for f in futures:
                        f.cancel()
                    # Don't break - let already-running futures complete quietly
                    # They will check cancel_flag and exit early
                if cancelled:
                    continue  # Don't process results after cancellation
                try:
                    future.result()
                except Exception as e:
                    if not self.cancel_flag.is_set():
                        self._log(f"Error in future result: {e}", "error")

    def get_progress_updates(self):
        """Get all pending progress updates from queue (non-blocking)."""
        updates = []
        while not self.progress_queue.empty():
            try:
                update = self.progress_queue.get_nowait()
                updates.append(update)
            except:
                break
        return updates

    def pause_processing(self):
        """Pause the current batch processing."""
        self.resume_event.clear()  # Clear event = pause

    def resume_processing(self):
        """Resume the paused batch processing."""
        self.resume_event.set()  # Set event = resume

    def cancel_processing(self):
        """Cancel the current batch processing."""
        self.cancel_flag.set()
        self.resume_event.set()  # Ensure threads aren't blocked on pause when canceling

    def cleanup(self):
        """Clean up resources."""
        self.cancel_flag.set()
        if hasattr(self, 'driver_pool'):
            self.driver_pool.cleanup()
