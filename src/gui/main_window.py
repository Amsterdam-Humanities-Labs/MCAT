"""
Main window for MCAT application.

Initializes DearPyGui, sets up theming, and runs the main event loop.
Uses AppController for screen navigation.
"""

import dearpygui.dearpygui as dpg
from typing import Optional
from pathlib import Path

from gui.app_controller import AppController
from gui.themes.noctua_theme import create_noctua_theme
from services.processing_service import ProcessingService
from utils.console_logger import ConsoleLogger


# Font configuration
# Path: main_window.py -> gui -> src -> MCAT -> assets
FONT_PATH = Path(__file__).parent.parent.parent / "assets" / "IBMPlexMono-Regular.ttf"
FONT_SIZE = 18  # Desired size
FONT_SCALE_FACTOR = 2  # Load at 2x, then scale down for crisp rendering


class MainWindow:
    """Primary GUI controller using Dear PyGui."""

    def __init__(self):
        self.console_logger: Optional[ConsoleLogger] = None
        self.app_controller: Optional[AppController] = None

        # UI element IDs
        self.main_window_id = "main_window"

        # Track viewport size for resize detection
        self._last_viewport_width = 0
        self._last_viewport_height = 0

    def setup_ui(self):
        """Create the main window and initialize app controller."""
        # Create main window
        with dpg.window(
            tag=self.main_window_id,
            label="",
            width=1000,
            height=800,
            pos=[50, 50]
        ):
            pass  # Content managed by AppController

        # Initialize app controller
        self.app_controller = AppController(self.main_window_id)
        self.app_controller.setup()

    def _check_viewport_resize(self):
        """Check if viewport was resized and notify app controller."""
        current_width = dpg.get_viewport_client_width()
        current_height = dpg.get_viewport_client_height()

        if (current_width != self._last_viewport_width or
            current_height != self._last_viewport_height):
            self._last_viewport_width = current_width
            self._last_viewport_height = current_height

            # Notify app controller to re-center cards
            if self.app_controller:
                self.app_controller.handle_viewport_resize()

    def run(self):
        """Start the GUI application with progress processing main loop."""
        # Initialize console logger to capture print statements
        self.console_logger = ConsoleLogger()
        self.console_logger.install()

        dpg.create_context()
        dpg.configure_app(manual_callback_management=True)
        dpg.create_viewport(title="MCAT - Moderation Content Analysis Tool", width=1100, height=850)

        # Load custom font at 2x size, then scale down for crisp rendering
        if FONT_PATH.exists():
            with dpg.font_registry():
                default_font = dpg.add_font(str(FONT_PATH), FONT_SIZE * FONT_SCALE_FACTOR)
            dpg.bind_font(default_font)
            dpg.set_global_font_scale(1.0 / FONT_SCALE_FACTOR)
        else:
            print(f"Font not found: {FONT_PATH}, using default")

        # Apply Noctua theme
        noctua_theme = create_noctua_theme()
        dpg.bind_theme(noctua_theme)

        self.setup_ui()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.main_window_id, True)

        # Store initial viewport size
        self._last_viewport_width = dpg.get_viewport_client_width()
        self._last_viewport_height = dpg.get_viewport_client_height()

        try:
            # Main event loop with progress processing
            while dpg.is_dearpygui_running():
                # Process Dear PyGui callbacks
                jobs = dpg.get_callback_queue()
                dpg.run_callbacks(jobs)

                # Process progress updates from all ProcessingService instances
                ProcessingService.process_all_progress_updates()

                # Check for viewport resize
                self._check_viewport_resize()

                # Render frame
                dpg.render_dearpygui_frame()
        finally:
            # Uninstall console logger
            if self.console_logger:
                self.console_logger.uninstall()

            # Cleanup app controller
            if self.app_controller:
                self.app_controller.cleanup()

            dpg.destroy_context()
