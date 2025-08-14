import os
import threading
import time
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller


class WebDriverPool:
    """Thread-safe WebDriver pool for reusing browser instances."""
    
    def __init__(self, pool_size: int, headless: bool = True):
        self.pool_size = pool_size
        self.headless = headless
        self.chromedriver_path = None
        self._setup_chromedriver()
        
        # Thread-safe driver pool
        self.available_drivers = Queue()
        self.all_drivers = []
        self.lock = threading.Lock()
        
        # Initialize the pool
        self._initialize_pool()
    
    def _setup_chromedriver(self):
        """Install and setup ChromeDriver automatically."""
        try:
            self.chromedriver_path = chromedriver_autoinstaller.install()
            print(f"ChromeDriver installed at: {self.chromedriver_path}")
        except Exception as e:
            raise Exception(f"Failed to install ChromeDriver: {e}")
    
    def _create_driver_options(self) -> Options:
        """Create Chrome options for driver instances."""
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
        
        # Disable audio/video to prevent YouTube sound and reduce CPU usage
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--disable-audio-output")
        chrome_options.add_argument("--disable-background-media-download")
        chrome_options.add_argument("--disable-media-device-discovery")
        chrome_options.add_argument("--disable-media-session-api")
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        
        # User agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        return chrome_options
    
    def _initialize_pool(self):
        """Initialize the driver pool with browser instances."""
        print(f"Initializing WebDriver pool with {self.pool_size} instances...")
        chrome_options = self._create_driver_options()
        service = Service(self.chromedriver_path)
        
        for i in range(self.pool_size):
            try:
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.set_page_load_timeout(30)
                self.all_drivers.append(driver)
                self.available_drivers.put(driver)
                print(f"WebDriver {i+1}/{self.pool_size} initialized")
            except Exception as e:
                print(f"Failed to create WebDriver {i+1}: {e}")
                break
    
    def get_driver(self, timeout: int = 30) -> webdriver.Chrome:
        """Get a driver from the pool (blocks if none available)."""
        try:
            # Get driver from pool (blocks until available)
            driver = self.available_drivers.get(timeout=timeout)
            return driver
        except:
            raise Exception("No WebDriver available in pool (timeout)")
    
    def return_driver(self, driver: webdriver.Chrome):
        """Return a driver to the pool."""
        if driver and driver in self.all_drivers:
            # Clear any leftover state
            try:
                driver.delete_all_cookies()
                driver.execute_script("window.localStorage.clear();")
                driver.execute_script("window.sessionStorage.clear();")
            except:
                pass
            
            self.available_drivers.put(driver)
    
    def cleanup(self):
        """Clean up all drivers in the pool."""
        print("Cleaning up WebDriver pool...")
        with self.lock:
            # Close all drivers
            for driver in self.all_drivers:
                try:
                    driver.quit()
                except:
                    pass
            
            self.all_drivers.clear()
            
            # Clear the queue
            while not self.available_drivers.empty():
                try:
                    self.available_drivers.get_nowait()
                except:
                    break


class WebDriverManager:
    """Manages Chrome WebDriver instances with proper configuration and cleanup."""
    
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
        """Create a new Chrome WebDriver instance with optimized settings."""
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
        
        # Disable audio/video to prevent YouTube sound and reduce CPU usage
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--disable-audio-output")
        chrome_options.add_argument("--disable-background-media-download")
        chrome_options.add_argument("--disable-media-device-discovery")
        chrome_options.add_argument("--disable-media-session-api")
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        
        # User agent to avoid detection
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        service = Service(self.chromedriver_path)
        
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            raise Exception(f"Failed to create Chrome driver: {e}")
    
    def cleanup_driver(self, driver: webdriver.Chrome):
        """Clean up a specific driver instance."""
        try:
            if driver:
                driver.quit()
        except:
            pass
    
    @staticmethod
    def cleanup_all_processes():
        """Kill any leftover Chrome/ChromeDriver processes."""
        try:
            os.system('killall -9 chrome 2>/dev/null')
            os.system('killall -9 chromedriver 2>/dev/null')
        except:
            pass