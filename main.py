import dearpygui.dearpygui as dpg
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import threading
import time

class WebScraper:
    def __init__(self):
        self.url = "https://matussolcany.com"
        self.scraped_data = None
        self.is_scraping = False
        
    def scrape_website(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            # Use ChromeDriverManager to automatically download and manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            return {
                "error": f"ChromeDriver setup failed: {str(e)}",
                "url": self.url
            }
        
        try:
            driver.get(self.url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            title = driver.title
            body_text = driver.find_element(By.TAG_NAME, "body").text
            
            return {
                "title": title,
                "content": body_text,
                "url": self.url
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "url": self.url
            }
        
        finally:
            driver.quit()
    
    def scrape_threaded(self, *args, **kwargs):
        if self.is_scraping:
            return
            
        self.is_scraping = True
        dpg.set_value("status_text", "Scraping website... Please wait.")
        dpg.configure_item("scrape_button", enabled=False)
        
        def scrape_task():
            try:
                self.scraped_data = self.scrape_website()
                
                if "error" in self.scraped_data:
                    dpg.set_value("status_text", f"Error: {self.scraped_data['error']}")
                    dpg.set_value("result_text", "")
                else:
                    dpg.set_value("status_text", "Scraping completed successfully!")
                    content = self.scraped_data['content']
                    truncated_content = content[:1000] + ('...' if len(content) > 1000 else '')
                    result = f"Title: {self.scraped_data['title']}\n\nContent:\n{truncated_content}"
                    dpg.set_value("result_text", result)
                    
            except Exception as e:
                dpg.set_value("status_text", f"Unexpected error: {str(e)}")
                dpg.set_value("result_text", "")
            
            finally:
                self.is_scraping = False
                dpg.configure_item("scrape_button", enabled=True)
        
        thread = threading.Thread(target=scrape_task)
        thread.daemon = True
        thread.start()

def main():
    scraper = WebScraper()
    
    dpg.create_context()
    dpg.create_viewport(title="Selenium + DearPyGui Web Scraper", width=900, height=600)
    
    with dpg.window(label="Web Scraper", width=880, height=580, pos=[10, 10]):
        dpg.add_text("Selenium + DearPyGui Web Scraper", tag="title_text")
        dpg.add_text(f"Target URL: {scraper.url}", tag="url_text")
        dpg.add_separator()
        
        dpg.add_button(label="Scrape Website", tag="scrape_button", 
                      callback=scraper.scrape_threaded, width=200)
        
        dpg.add_separator()
        dpg.add_text("Click 'Scrape Website' to fetch content from matussolcany.com", 
                    tag="status_text")
        dpg.add_separator()
        
        with dpg.child_window(label="Results", width=850, height=380):
            dpg.add_input_text(tag="result_text", multiline=True, 
                             width=830, height=360, readonly=True)
    
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
