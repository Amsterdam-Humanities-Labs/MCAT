"""
MCAT Selenium App - Main Entry Point
====================================

Content Moderation Analysis Toolkit (MCAT) desktop application
for processing CSV files containing social media URLs and checking
their moderation status.

Usage:
    python -m src.main
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow


def main():
    """Main application entry point."""
    try:
        print("Starting MCAT GUI Application...")
        print("CSV Loading Test Mode")
        print("-" * 40)
        
        # Create and run the main window
        app = MainWindow()
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())