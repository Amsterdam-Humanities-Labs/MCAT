import pandas as pd
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


class ProcessingResult:
    """Result container for batch processing operations."""
    
    def __init__(self):
        self.success: bool = False
        self.dataframe: Optional[pd.DataFrame] = None
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
        
        # Initialize WebDriver pool
        self.driver_pool = WebDriverPool(
            pool_size=self.max_workers,
            headless=config.scraper_settings['headless']
        )
        
        # Thread-safe progress queue for GUI updates
        self.progress_queue = Queue()
        self.progress_callback = None
    
    def process_csv(self, csv_path: str, platform: str, column_mapping: Dict[str, str],
                   output_folder: str = None, save_screenshots: bool = False) -> ProcessingResult:
        """Process a CSV file of URLs with incremental saving."""
        result = ProcessingResult()
        csv_writer = None
        output_csv_path = None

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

            # Step 6: Process URLs with incremental writing
            self._process_batch(urls, scraper, csv_writer, df, url_column)

            if self.cancel_flag.is_set():
                result.error_message = "Processing was cancelled"
                # Still load partial results from CSV if available
                if output_csv_path and output_csv_path.exists():
                    result.dataframe = pd.read_csv(output_csv_path)
                return result

            # Step 7: Load CSV back into memory for GUI table
            if output_csv_path and output_csv_path.exists():
                result.dataframe = pd.read_csv(output_csv_path)
            else:
                # Fallback if no CSV was saved (shouldn't happen)
                result.dataframe = df

            # Calculate final stats from loaded DataFrame
            if result.dataframe is not None:
                status_counts = result.dataframe['status'].value_counts().to_dict()
                result.stats = {
                    'live': status_counts.get('Live', 0),
                    'removed': status_counts.get('Removed', 0),
                    'restricted': status_counts.get('Restricted', 0) + status_counts.get('Age-restricted', 0) +
                                  status_counts.get('Geo-blocked', 0) + status_counts.get('Private', 0),
                    'errors': status_counts.get('Error', 0)
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
        if platform == 'youtube':
            scraper = YouTubeScraper(self.driver_pool)
            # Set resume event for efficient pause control
            scraper.set_pause_event(self.resume_event)
            return scraper
        return None
    
    def set_progress_callback(self, callback):
        """Set callback function for progress updates."""
        self.progress_callback = callback
    
    def _process_batch(self, urls: List[str], scraper,
                      csv_writer: Optional[IncrementalCSVWriter] = None,
                      original_df: Optional[pd.DataFrame] = None,
                      url_column: str = None) -> None:
        """Process URLs in parallel batches with incremental CSV writing."""
        processed = 0
        total = len(urls)

        # Thread-safe counters
        stats_lock = threading.Lock()
        stats = {'live': 0, 'removed': 0, 'restricted': 0, 'errors': 0, 'skipped': 0}

        def process_single_url(url: str, row_index: int) -> None:
            nonlocal processed
            if self.cancel_flag.is_set():
                return

            try:
                # Check URL using shared scraper
                result = scraper.check_url_status(url)

                # Write to CSV incrementally if writer provided
                if csv_writer and original_df is not None:
                    # Get original row data
                    original_row = original_df.iloc[row_index].to_dict()
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

                # Queue progress update for main thread
                progress_data = {
                    'current': current_processed,
                    'total': total,
                    'stats': current_stats,
                    'current_action': f"Checking: {url[:60]}{'...' if len(url) > 60 else ''}"
                }
                self.progress_queue.put(progress_data)

            except Exception as e:
                print(f"Error processing URL {url}: {e}")
                with stats_lock:
                    stats['errors'] += 1
                    processed += 1

        # Process URLs with threading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(process_single_url, url, idx) for idx, url in enumerate(urls)]

            for future in as_completed(futures):
                if self.cancel_flag.is_set():
                    break
                try:
                    future.result()
                except Exception as e:
                    print(f"Error in future result: {e}")
    
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