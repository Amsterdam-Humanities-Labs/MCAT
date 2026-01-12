"""
MCAT Selenium App - Main Entry Point
====================================

Content Moderation Analysis Toolkit (MCAT) desktop application
for processing CSV files containing social media URLs and checking
their moderation status.

"""

import sys
import os
import signal
import atexit

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
from core.driver_manager import WebDriverManager

# Global app instance for cleanup
app_instance = None

def cleanup_on_exit():
    """Cleanup function called on application exit."""
    print("\n🧹 Cleaning up application...")
    
    # Suppress urllib3 warnings during cleanup (expected when ChromeDrivers are killed)
    import urllib3
    import logging
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
    
    try:
        # Cleanup app components - WebDriverPool.cleanup() will call driver.quit()
        if app_instance:
            if hasattr(app_instance, 'processing_controller') and app_instance.processing_controller:
                app_instance.processing_controller.cleanup()
        
        # Note: Relying on Selenium's driver.quit() for cross-platform cleanup
        WebDriverManager.cleanup_all_processes()
        print("✅ Application cleanup completed")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

def signal_handler(signum, frame):
    """Handle termination signals."""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    cleanup_on_exit()
    sys.exit(0)

def main():
    """Main application entry point."""
    global app_instance
    
    # Register cleanup handlers
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination request
    
    try:
        print("Starting MCAT GUI Application...")
        
        # Create and run the main window
        app_instance = MainWindow()
        app_instance.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        cleanup_on_exit()
    except Exception as e:
        import traceback
        print(f"Error starting application: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        cleanup_on_exit()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
