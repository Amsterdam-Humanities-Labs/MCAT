import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from utils.state_manager import StateManager, ProcessingState
from utils.csv_handler import CSVHandler
from core.driver_manager import WebDriverManager
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
    """Main processing pipeline coordinator."""
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.cancel_flag = threading.Event()
        self.max_workers = config.scraper_settings['max_workers']
        self.driver_manager = WebDriverManager(headless=config.scraper_settings['headless'])
    
    def process_csv(self, csv_path: str, platform: str, column_mapping: Dict[str, str], 
                   output_path: str = None) -> ProcessingResult:
        """Process a CSV file of URLs."""
        result = ProcessingResult()
        
        try:
            # Reset cancel flag
            self.cancel_flag.clear()
            
            # Step 1: Load CSV
            self.state_manager.broadcast_state(ProcessingState.LOADING_CSV)
            df = CSVHandler.load_csv(csv_path)
            
            # Step 2: Validate data
            self.state_manager.broadcast_state(ProcessingState.VALIDATING_DATA)
            valid, error_msg = CSVHandler.validate_column_mapping(df, column_mapping)
            if not valid:
                result.error_message = error_msg
                self.state_manager.broadcast_state(ProcessingState.ERROR)
                return result
            
            # Add result columns
            df = CSVHandler.add_result_columns(df)
            
            # Step 3: Initialize scraper
            self.state_manager.broadcast_state(ProcessingState.INITIALIZING_SCRAPERS)
            scraper = self._create_scraper(platform)
            if not scraper:
                result.error_message = f"Unsupported platform: {platform}"
                self.state_manager.broadcast_state(ProcessingState.ERROR)
                return result
            
            # Step 4: Extract URLs
            url_column = column_mapping.get('post', '')
            urls = CSVHandler.get_urls_from_column(df, url_column)
            
            # Step 5: Process URLs
            self.state_manager.broadcast_state(ProcessingState.PROCESSING_URLS)
            scraping_results = self._process_batch(urls, scraper)
            
            if self.cancel_flag.is_set():
                result.error_message = "Processing was cancelled"
                self.state_manager.broadcast_state(ProcessingState.CANCELLED)
                return result
            
            # Step 6: Update DataFrame with results
            self.state_manager.broadcast_state(ProcessingState.FINALIZING_RESULTS)
            df = CSVHandler.update_results(df, scraping_results, url_column)
            
            # Step 7: Save if output path provided
            if output_path:
                CSVHandler.save_csv(df, output_path)
            
            # Calculate final stats
            status_counts = df['status'].value_counts().to_dict()
            result.stats = {
                'live': status_counts.get('Live', 0),
                'removed': status_counts.get('Removed', 0) + status_counts.get('Age-restricted', 0) + 
                          status_counts.get('Geo-blocked', 0) + status_counts.get('Private', 0),
                'restricted': status_counts.get('Restricted', 0),
                'errors': status_counts.get('Error', 0)
            }
            
            result.success = True
            result.dataframe = df
            result.processed_count = len(scraping_results)
            
            self.state_manager.broadcast_state(ProcessingState.COMPLETED, {
                'stats': result.stats,
                'current': result.processed_count,
                'total': len(urls)
            })
            
        except Exception as e:
            result.error_message = str(e)
            self.state_manager.broadcast_state(ProcessingState.ERROR)
        
        finally:
            # Cleanup
            if 'scraper' in locals():
                scraper.cleanup()
        
        return result
    
    def _create_scraper(self, platform: str):
        """Create a scraper instance for the specified platform."""
        if platform == 'youtube':
            return YouTubeScraper(self.driver_manager)
        return None
    
    def _process_batch(self, urls: List[str], scraper) -> List[Dict]:
        """Process URLs in parallel batches."""
        results = []
        processed = 0
        total = len(urls)
        
        stats = {'live': 0, 'removed': 0, 'restricted': 0, 'errors': 0}
        
        def process_single_url(url: str) -> Dict:
            nonlocal processed
            if self.cancel_flag.is_set():
                return None
            
            # Check URL
            result = scraper.check_url_status(url)
            result_dict = result.to_dict()
            
            # Update stats
            status = result.status.lower()
            if status == 'live':
                stats['live'] += 1
            elif status in ['removed', 'age-restricted', 'geo-blocked', 'private']:
                stats['removed'] += 1
            elif status == 'restricted':
                stats['restricted'] += 1
            else:
                stats['errors'] += 1
            
            processed += 1
            
            # Update progress
            self.state_manager.update_progress(
                current=processed,
                total=total,
                stats=stats.copy(),
                current_action=f"Checking: {url[:60]}{'...' if len(url) > 60 else ''}"
            )
            
            return result_dict
        
        # Process URLs with threading
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(process_single_url, url) for url in urls]
            
            for future in as_completed(futures):
                if self.cancel_flag.is_set():
                    break
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error in processing: {e}")
        
        return results
    
    def cancel_processing(self):
        """Cancel the current batch processing."""
        self.cancel_flag.set()
    
    def cleanup(self):
        """Clean up resources."""
        self.cancel_flag.set()
        WebDriverManager.cleanup_all_processes()