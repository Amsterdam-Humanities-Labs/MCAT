import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller


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