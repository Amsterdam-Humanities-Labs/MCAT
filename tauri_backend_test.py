"""
Minimal backend test for Tauri bundle size estimation.
Imports the same deps MCAT uses (minus dearpygui).
"""

# Core deps that would be needed in Tauri backend
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import chromedriver_autoinstaller
from pydispatch import dispatcher

# Standard library (included anyway)
import threading
import json
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "pandas": pd.__version__}

def main():
    print("MCAT Backend Test")
    print(f"Pandas version: {pd.__version__}")
    print("Ready for Tauri integration")

if __name__ == "__main__":
    main()
