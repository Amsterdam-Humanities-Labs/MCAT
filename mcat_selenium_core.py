"""
MCAT Selenium Core - Content Moderation Analysis Toolkit
========================================================

This module contains the core Selenium functionality extracted from the MCAT Jupyter notebook
for checking content moderation status across social media platforms.

Core Features:
1. Multi-Platform Content Status Checking (Facebook, YouTube, Twitter, TikTok)
2. Batch URL Processing with multi-threading
3. Robust WebDriver management and automation

Author: Extracted from MCAT Toolkit
License: Research/Educational Use
"""

import os
import time
import logging
import threading
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import chromedriver_autoinstaller

# Suppress warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.getLogger('selenium').setLevel(logging.CRITICAL)


class WebDriverManager:
    """
    Manages Chrome WebDriver instances with proper configuration and cleanup.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.chromedriver_path = None
        self._setup_chromedriver()
    
    def _setup_chromedriver(self):
        """Install and setup ChromeDriver automatically."""
        try:
            self.chromedriver_path = chromedriver_autoinstaller.install()
            print(f"ChromeDriver installed at: {self.chromedriver_path}")
        except Exception as e:
            raise Exception(f"Failed to install ChromeDriver: {e}")
    
    def create_driver(self) -> webdriver.Chrome:
        """
        Create a new Chrome WebDriver instance with optimized settings.
        
        Returns:
            webdriver.Chrome: Configured Chrome driver instance
        """
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Performance and stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--incognito")
        
        # User agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = Service(self.chromedriver_path)
        
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            raise Exception(f"Failed to create Chrome driver: {e}")
    
    @staticmethod
    def cleanup_processes():
        """Kill any leftover Chrome/ChromeDriver processes."""
        try:
            os.system('killall -9 chrome 2>/dev/null')
            os.system('killall -9 chromedriver 2>/dev/null')
        except:
            pass


class FacebookChecker:
    """
    Checks Facebook/Instagram post status for content moderation.
    """
    
    def __init__(self, driver_manager: WebDriverManager):
        self.driver_manager = driver_manager
        self.moderation_selectors = [
            'div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.xbxaen2.x1u72gb5.x1t1ogtf.x13zrc24.x1n2onr6.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.xl56j7k',
            # Add more Facebook moderation selectors here
        ]
    
    def check_post_status(self, url: str) -> str:
        """
        Check the status of a Facebook/Instagram post.
        
        Args:
            url (str): The Facebook/Instagram post URL
            
        Returns:
            str: Status - "Live", "Removed", "Restricted", "Error"
        """
        driver = None
        try:
            driver = self.driver_manager.create_driver()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for moderation indicators
            for selector in self.moderation_selectors:
                try:
                    elements = WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if elements:
                        return "Removed"
                except TimeoutException:
                    continue
            
            # Check page title for error indicators
            title = driver.title.lower()
            if any(keyword in title for keyword in ['error', 'not found', 'unavailable']):
                return "Removed"
            
            # If no moderation indicators found, assume live
            return "Live"
            
        except Exception as e:
            print(f"Error checking Facebook URL {url}: {e}")
            return "Error"
        finally:
            if driver:
                driver.quit()


class YouTubeChecker:
    """
    Checks YouTube video status for content moderation, age restrictions, etc.
    """
    
    def __init__(self, driver_manager: WebDriverManager):
        self.driver_manager = driver_manager
    
    def check_video_status(self, url: str) -> Tuple[str, str]:
        """
        Check the status of a YouTube video.
        
        Args:
            url (str): The YouTube video URL
            
        Returns:
            Tuple[str, str]: (status, info_panel) - Status and additional info
        """
        driver = None
        try:
            driver = self.driver_manager.create_driver()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for various YouTube error/restriction indicators
            page_source = driver.page_source.lower()
            
            # Video removed/unavailable
            if any(phrase in page_source for phrase in [
                'video unavailable', 'this video is not available', 
                'removed by the user', 'account has been terminated'
            ]):
                return "Removed", "Video unavailable"
            
            # Age restricted
            if 'age-restricted' in page_source or 'sign in to confirm your age' in page_source:
                return "Age-restricted", "Age verification required"
            
            # Geo-blocked
            if 'not available in your country' in page_source:
                return "Geo-blocked", "Not available in your region"
            
            # Private video
            if 'private video' in page_source:
                return "Private", "Video is private"
            
            # Check for content warning panels
            try:
                warning_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="warning"], [class*="restricted"]')
                if warning_elements:
                    warning_text = warning_elements[0].text
                    return "Restricted", f"Warning: {warning_text[:100]}"
            except:
                pass
            
            # If no restrictions found, assume live
            return "Live", "Video available"
            
        except Exception as e:
            print(f"Error checking YouTube URL {url}: {e}")
            return "Error", str(e)
        finally:
            if driver:
                driver.quit()


class TwitterChecker:
    """
    Checks Twitter/X post status for content moderation.
    """
    
    def __init__(self, driver_manager: WebDriverManager):
        self.driver_manager = driver_manager
    
    def check_tweet_status(self, url: str) -> str:
        """
        Check the status of a Twitter/X post.
        
        Args:
            url (str): The Twitter/X post URL
            
        Returns:
            str: Status - "Live", "Deleted", "Suspended", "Protected", "Error"
        """
        driver = None
        try:
            driver = self.driver_manager.create_driver()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            page_source = driver.page_source.lower()
            
            # Check for various Twitter error indicators
            if 'this post is from an account that no longer exists' in page_source:
                return "Deleted"
            
            if 'account suspended' in page_source:
                return "Suspended"
            
            if 'protected tweets' in page_source or 'these tweets are protected' in page_source:
                return "Protected"
            
            if 'page does not exist' in page_source or 'sorry, that page does not exist' in page_source:
                return "Deleted"
            
            # Check if we can find tweet content
            try:
                tweet_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweet"]')
                if tweet_elements:
                    return "Live"
                else:
                    return "Deleted"
            except:
                return "Error"
            
        except Exception as e:
            print(f"Error checking Twitter URL {url}: {e}")
            return "Error"
        finally:
            if driver:
                driver.quit()


class TikTokChecker:
    """
    Checks TikTok video status for content moderation.
    """
    
    def __init__(self, driver_manager: WebDriverManager):
        self.driver_manager = driver_manager
    
    def check_video_status(self, url: str) -> str:
        """
        Check the status of a TikTok video.
        
        Args:
            url (str): The TikTok video URL
            
        Returns:
            str: Status - "Live", "Removed", "Private", "Error"
        """
        driver = None
        try:
            driver = self.driver_manager.create_driver()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            page_source = driver.page_source.lower()
            
            # Check for TikTok error indicators
            if any(phrase in page_source for phrase in [
                'video currently unavailable', 'this video is not available',
                'content not available', 'video has been removed'
            ]):
                return "Removed"
            
            if 'private account' in page_source:
                return "Private"
            
            # Check for video player or content
            try:
                video_elements = driver.find_elements(By.CSS_SELECTOR, 'video, [class*="video"]')
                if video_elements:
                    return "Live"
                else:
                    return "Removed"
            except:
                return "Error"
            
        except Exception as e:
            print(f"Error checking TikTok URL {url}: {e}")
            return "Error"
        finally:
            if driver:
                driver.quit()


class BatchProcessor:
    """
    Processes multiple URLs in batches using multi-threading.
    """
    
    def __init__(self, max_workers: int = 10, headless: bool = True):
        self.max_workers = max_workers
        self.driver_manager = WebDriverManager(headless=headless)
        self.cancel_flag = threading.Event()
        
        # Initialize platform checkers
        self.facebook_checker = FacebookChecker(self.driver_manager)
        self.youtube_checker = YouTubeChecker(self.driver_manager)
        self.twitter_checker = TwitterChecker(self.driver_manager)
        self.tiktok_checker = TikTokChecker(self.driver_manager)
    
    def detect_platform(self, url: str) -> str:
        """
        Detect which platform a URL belongs to.
        
        Args:
            url (str): The URL to analyze
            
        Returns:
            str: Platform name or "unknown"
        """
        url = url.lower()
        
        if 'facebook.com' in url or 'fb.com' in url:
            return 'facebook'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        elif 'tiktok.com' in url:
            return 'tiktok'
        else:
            return 'unknown'
    
    def check_single_url(self, url: str, platform: str = None) -> Dict[str, str]:
        """
        Check the status of a single URL.
        
        Args:
            url (str): The URL to check
            platform (str, optional): Platform name, auto-detected if None
            
        Returns:
            Dict[str, str]: Result dictionary with status info
        """
        if platform is None:
            platform = self.detect_platform(url)
        
        result = {
            'url': url,
            'platform': platform,
            'status': 'Unknown',
            'info': '',
            'date_checked': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'error': ''
        }
        
        try:
            if platform == 'facebook' or platform == 'instagram':
                result['status'] = self.facebook_checker.check_post_status(url)
            elif platform == 'youtube':
                status, info = self.youtube_checker.check_video_status(url)
                result['status'] = status
                result['info'] = info
            elif platform == 'twitter':
                result['status'] = self.twitter_checker.check_tweet_status(url)
            elif platform == 'tiktok':
                result['status'] = self.tiktok_checker.check_video_status(url)
            else:
                result['status'] = 'Unsupported Platform'
                result['error'] = f'Platform {platform} not supported'
                
        except Exception as e:
            result['status'] = 'Error'
            result['error'] = str(e)
        
        return result
    
    def process_csv(self, csv_path: str, url_column: str = 'URL', 
                   output_path: str = None, progress_callback=None) -> pd.DataFrame:
        """
        Process a CSV file of URLs in batches.
        
        Args:
            csv_path (str): Path to input CSV file
            url_column (str): Name of the URL column
            output_path (str, optional): Path to save results
            progress_callback (callable, optional): Progress update function
            
        Returns:
            pd.DataFrame: Results dataframe
        """
        try:
            # Load CSV
            df = pd.read_csv(csv_path)
            if url_column not in df.columns:
                raise ValueError(f"Column '{url_column}' not found in CSV")
            
            # Add result columns
            result_columns = ['status', 'platform', 'info', 'date_checked', 'error']
            for col in result_columns:
                if col not in df.columns:
                    df[col] = ''
            
            total_urls = len(df)
            processed = 0
            
            def process_row(index, row):
                nonlocal processed
                if self.cancel_flag.is_set():
                    return
                
                url = row[url_column]
                result = self.check_single_url(url)
                
                # Update dataframe
                for key, value in result.items():
                    if key in df.columns:
                        df.at[index, key] = value
                
                processed += 1
                if progress_callback:
                    progress_callback(processed, total_urls)
                
                print(f"[{processed}/{total_urls}] {url} -> {result['status']}")
            
            # Process URLs with threading
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(process_row, index, row) 
                          for index, row in df.iterrows()]
                
                for future in as_completed(futures):
                    if self.cancel_flag.is_set():
                        break
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error in processing: {e}")
            
            # Save results
            if output_path:
                df.to_csv(output_path, index=False)
                print(f"Results saved to: {output_path}")
            
            return df
            
        except Exception as e:
            raise Exception(f"Error processing CSV: {e}")
    
    def cancel_processing(self):
        """Cancel the current batch processing."""
        self.cancel_flag.set()
    
    def cleanup(self):
        """Clean up resources and processes."""
        self.cancel_flag.set()
        WebDriverManager.cleanup_processes()


# Example usage and testing
if __name__ == "__main__":
    # Example of how to use the classes
    
    # Initialize batch processor
    processor = BatchProcessor(max_workers=5, headless=True)
    
    # Test single URL
    test_url = "https://www.youtube.com/watch?v=example"
    result = processor.check_single_url(test_url)
    print(f"Single URL result: {result}")
    
    # Test CSV processing (uncomment to use)
    # df_results = processor.process_csv('input_urls.csv', 'URL', 'output_results.csv')
    # print(f"Processed {len(df_results)} URLs")
    
    # Cleanup
    processor.cleanup()