import dearpygui.dearpygui as dpg
from typing import Optional
from pathlib import Path

from gui.components.containers.tab_container_platforms import PlatformTabs
from gui.components.panels.panel_console import ConsolePanel
from presenters.console_presenter import ConsolePresenter
from services.processing_service import ProcessingService
from gui.theme import AppTheme
from gui.themes.noctua_theme import create_noctua_theme
from utils.console_logger import ConsoleLogger


# Font configuration
# Path: main_window.py -> gui -> src -> MCAT -> assets
FONT_PATH = Path(__file__).parent.parent.parent / "assets" / "IBMPlexMono-Regular.ttf"
FONT_SIZE = 30  # Desired size
FONT_SCALE_FACTOR = 2  # Load at 2x, then scale down to 0.5 for crisp rendering


class MainWindow:
    """Primary GUI controller using Dear PyGui."""
    
    def __init__(self):
        self.console_logger: Optional[ConsoleLogger] = None
        self.console_presenter: Optional[ConsolePresenter] = None
        self.platform_tabs: Optional[PlatformTabs] = None

        # UI element IDs
        self.main_window_id = "main_window"
    
    def setup_ui(self):
        """Create the main window UI."""
        # Create main window
        with dpg.window(
            tag=self.main_window_id,
            label="",
            width=1000,
            height=800,
            pos=[50, 50]
        ):
            # Vertical layout: tabs on top, console on bottom
            # Platform Tabs (flexible height - account for console at bottom)
            # Height calculation: 800px window - 230px console section (200px + header + spacers)
            with dpg.child_window(
                tag="tabs_container",
                height=565,  # Fixed height to prevent overflow
                border=False,
                horizontal_scrollbar=False
            ):
                self.platform_tabs = PlatformTabs(
                    parent_window="tabs_container"
                )
                self.platform_tabs.setup_ui()

            # Small spacer for visual separation
            dpg.add_spacer(height=5, parent=self.main_window_id)

            # Global console view (fixed height, full width)
            console_view = ConsolePanel(
                parent_window=self.main_window_id,
                platform="global"
            )
            console_view.setup_ui()

            # Create console presenter (MVP: coordinates logger service and console view)
            self.console_presenter = ConsolePresenter(
                view=console_view,
                logger=self.console_logger
            )
            
    
    def run(self):
        """Start the GUI application with progress processing main loop."""
        # Initialize console logger to capture print statements
        self.console_logger = ConsoleLogger()
        self.console_logger.install()

        dpg.create_context()
        dpg.configure_app(manual_callback_management=True)  # Enable manual callback management
        dpg.create_viewport(title="MCAT Content Moderation Checker", width=1050, height=850)

        # Load custom font at 2x size, then scale down for crisp rendering
        if FONT_PATH.exists():
            with dpg.font_registry():
                default_font = dpg.add_font(str(FONT_PATH), FONT_SIZE * FONT_SCALE_FACTOR)
            dpg.bind_font(default_font)
            dpg.set_global_font_scale(1.0 / FONT_SCALE_FACTOR)
        else:
            print(f"⚠️ Font not found: {FONT_PATH}, using default")

        # Apply Noctua theme
        noctua_theme = create_noctua_theme()
        dpg.bind_theme(noctua_theme)

        self.setup_ui()
        
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window(self.main_window_id, True)
        
        try:
            # Main event loop with progress processing
            while dpg.is_dearpygui_running():
                # Process Dear PyGui callbacks
                jobs = dpg.get_callback_queue()
                dpg.run_callbacks(jobs)

                # Process progress updates from all ProcessingService instances
                ProcessingService.process_all_progress_updates()

                # Update global console with new messages (MVP: MainWindow → ConsolePresenter → ConsolePanel)
                if self.console_presenter:
                    self.console_presenter.update()

                # Render frame
                dpg.render_dearpygui_frame()
        finally:
            # Uninstall console logger
            if self.console_logger:
                self.console_logger.uninstall()

            # Cleanup components
            if self.platform_tabs:
                self.platform_tabs.cleanup()
            dpg.destroy_context()
 
    def _update_status(self, message: str, color: list = None):
        """Update the status display."""
        # Status display was removed, this method is kept for compatibility
        # but does nothing. Status is now shown in individual tabs.
        pass
    

