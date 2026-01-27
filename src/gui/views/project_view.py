"""
Project view - main view when a project is open.

Shows project info, run controls, progress, and results.
"""

import dearpygui.dearpygui as dpg
from typing import Callable, Optional, List
import pandas as pd

from models.project_models import RunConfig, RunStatus
from models.processing_models import ProcessingState
from gui.components.widgets.progress_bar_segmented import RectangularProgress
from gui.components.panels.panel_console import ConsolePanel
from gui.themes.noctua_theme import create_dark_container_theme


class ProjectView:
    """
    Main view for an open project.

    Layout:
    - Left panel: project info, run history, controls
    - Right panel: progress, results table, console
    """

    def __init__(self):
        self.container_id = "project_view"
        self.presenter: Optional[object] = None

        # UI element IDs
        self.left_panel_id = "pv_left_panel"
        self.right_panel_id = "pv_right_panel"
        self.project_name_id = "pv_project_name"
        self.project_info_id = "pv_project_info"
        self.run_history_id = "pv_run_history"
        self.start_btn_id = "pv_start_btn"
        self.pause_btn_id = "pv_pause_btn"
        self.resume_btn_id = "pv_resume_btn"
        self.cancel_btn_id = "pv_cancel_btn"
        self.screenshots_cb_id = "pv_screenshots_cb"
        self.results_table_id = "pv_results_table"
        self.progress_section_id = "pv_progress_section"

        # Components
        self.progress_display: Optional[RectangularProgress] = None
        self.console_panel: Optional[ConsolePanel] = None

        # Callbacks
        self._on_start_run: Optional[Callable] = None
        self._on_pause: Optional[Callable] = None
        self._on_resume: Optional[Callable] = None
        self._on_cancel: Optional[Callable] = None
        self._on_add_urls: Optional[Callable] = None
        self._on_close_project: Optional[Callable] = None

    def set_presenter(self, presenter) -> None:
        """Set the presenter for this view."""
        self.presenter = presenter

    def set_callbacks(
        self,
        on_start_run: Callable,
        on_pause: Callable,
        on_resume: Callable,
        on_cancel: Callable,
        on_add_urls: Callable,
        on_close_project: Callable
    ) -> None:
        """Set callback functions for user actions."""
        self._on_start_run = on_start_run
        self._on_pause = on_pause
        self._on_resume = on_resume
        self._on_cancel = on_cancel
        self._on_add_urls = on_add_urls
        self._on_close_project = on_close_project

    def setup_ui(self, parent: str) -> None:
        """Create the project view UI."""
        with dpg.group(tag=self.container_id, parent=parent, horizontal=True):
            self._setup_left_panel()
            self._setup_right_panel()

    def _setup_left_panel(self) -> None:
        """Setup left control panel."""
        with dpg.child_window(
            tag=self.left_panel_id,
            width=280,
            border=True
        ):
            # Project info section
            dpg.add_text("Project", color=[200, 200, 200])
            dpg.add_separator()

            dpg.add_text("", tag=self.project_name_id)
            dpg.add_text("", tag=self.project_info_id, color=[150, 150, 150])

            dpg.add_spacer(height=15)

            # Run controls section
            dpg.add_text("Run Controls", color=[200, 200, 200])
            dpg.add_separator()

            dpg.add_spacer(height=5)

            dpg.add_checkbox(
                label="Save screenshots",
                tag=self.screenshots_cb_id
            )

            dpg.add_spacer(height=10)

            # Control buttons
            dpg.add_button(
                label="Start Run",
                tag=self.start_btn_id,
                width=250,
                height=35,
                callback=self._handle_start_run
            )

            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Pause",
                    tag=self.pause_btn_id,
                    width=120,
                    height=30,
                    callback=self._handle_pause,
                    show=False
                )
                dpg.add_button(
                    label="Resume",
                    tag=self.resume_btn_id,
                    width=120,
                    height=30,
                    callback=self._handle_resume,
                    show=False
                )

            dpg.add_button(
                label="Cancel",
                tag=self.cancel_btn_id,
                width=250,
                height=30,
                callback=self._handle_cancel,
                show=False
            )

            dpg.add_spacer(height=15)

            # Run history section
            dpg.add_text("Run History", color=[200, 200, 200])
            dpg.add_separator()

            with dpg.child_window(
                tag=self.run_history_id,
                height=200,
                border=False
            ):
                dpg.add_text("No runs yet", color=[120, 120, 120])

            dpg.add_spacer(height=15)

            # Actions section
            dpg.add_text("Actions", color=[200, 200, 200])
            dpg.add_separator()

            dpg.add_spacer(height=5)

            dpg.add_button(
                label="Add URLs",
                width=250,
                height=30,
                callback=self._handle_add_urls
            )

            dpg.add_spacer(height=5)

            dpg.add_button(
                label="Close Project",
                width=250,
                height=30,
                callback=self._handle_close_project
            )

    def _setup_right_panel(self) -> None:
        """Setup right content panel."""
        with dpg.child_window(
            tag=self.right_panel_id,
            border=False
        ):
            # Progress section
            with dpg.group(tag=self.progress_section_id):
                dpg.add_text("Progress", color=[200, 200, 200])
                dpg.add_separator()

                # Progress bar
                self.progress_display = RectangularProgress(
                    parent_window=self.progress_section_id
                )
                self.progress_display.setup_ui()

            dpg.add_spacer(height=10)

            # Results section
            dpg.add_text("Results", color=[200, 200, 200])
            dpg.add_separator()

            with dpg.child_window(
                tag=self.results_table_id,
                height=300,
                border=True,
                horizontal_scrollbar=True
            ):
                dpg.add_text("No results yet. Start a run to see results here.",
                           color=[120, 120, 120])

            # Apply dark theme to results area
            dpg.bind_item_theme(self.results_table_id, create_dark_container_theme())

            dpg.add_spacer(height=10)

            # Console section
            self.console_panel = ConsolePanel(
                parent_window=self.right_panel_id,
                platform="project"
            )
            self.console_panel.setup_ui()

    def _handle_start_run(self, sender, app_data) -> None:
        """Handle Start Run button click."""
        if self._on_start_run:
            screenshots_enabled = dpg.get_value(self.screenshots_cb_id)
            self._on_start_run(screenshots_enabled)

    def _handle_pause(self, sender, app_data) -> None:
        """Handle Pause button click."""
        if self._on_pause:
            self._on_pause()

    def _handle_resume(self, sender, app_data) -> None:
        """Handle Resume button click."""
        if self._on_resume:
            self._on_resume()

    def _handle_cancel(self, sender, app_data) -> None:
        """Handle Cancel button click."""
        if self._on_cancel:
            self._on_cancel()

    def _handle_add_urls(self, sender, app_data) -> None:
        """Handle Add URLs button click."""
        if self._on_add_urls:
            self._on_add_urls()

    def _handle_close_project(self, sender, app_data) -> None:
        """Handle Close Project button click."""
        if self._on_close_project:
            self._on_close_project()

    def show_project_info(self, name: str, platform: str, url_count: int) -> None:
        """Display project information."""
        dpg.set_value(self.project_name_id, name)
        dpg.set_value(
            self.project_info_id,
            f"Platform: {platform.capitalize()}\nURLs: {url_count}"
        )

    def show_run_history(self, runs: List[RunConfig]) -> None:
        """Display run history."""
        if dpg.does_item_exist(self.run_history_id):
            dpg.delete_item(self.run_history_id, children_only=True)

            if not runs:
                dpg.add_text(
                    "No runs yet",
                    color=[120, 120, 120],
                    parent=self.run_history_id
                )
                return

            for run in reversed(runs):  # Most recent first
                status_color = self._get_status_color(run.status)
                status_icon = self._get_status_icon(run.status)

                with dpg.group(parent=self.run_history_id, horizontal=True):
                    dpg.add_text(status_icon, color=status_color)
                    dpg.add_text(run.id, color=[180, 180, 180])

    def _get_status_color(self, status: RunStatus) -> List[int]:
        """Get color for run status."""
        if status == RunStatus.COMPLETED:
            return [100, 255, 100]
        elif status == RunStatus.IN_PROGRESS:
            return [255, 200, 100]
        else:  # ABANDONED
            return [150, 150, 150]

    def _get_status_icon(self, status: RunStatus) -> str:
        """Get icon for run status."""
        if status == RunStatus.COMPLETED:
            return "[OK]"
        elif status == RunStatus.IN_PROGRESS:
            return "[..]"
        else:  # ABANDONED
            return "[--]"

    def show_progress(
        self,
        stats: dict,
        total: int,
        current: int,
        action: str
    ) -> None:
        """Update progress display."""
        if self.progress_display:
            self.progress_display.update(stats, total, current, action)

    def clear_progress(self) -> None:
        """Clear progress display."""
        if self.progress_display:
            self.progress_display.reset()

    def show_results(self, dataframe: pd.DataFrame) -> None:
        """Display results in table."""
        if dpg.does_item_exist(self.results_table_id):
            dpg.delete_item(self.results_table_id, children_only=True)

            if dataframe is None or dataframe.empty:
                dpg.add_text(
                    "No results yet. Start a run to see results here.",
                    color=[120, 120, 120],
                    parent=self.results_table_id
                )
                return

            # Create table
            columns = list(dataframe.columns)
            with dpg.table(
                parent=self.results_table_id,
                header_row=True,
                borders_innerH=True,
                borders_outerH=True,
                borders_innerV=True,
                borders_outerV=True,
                scrollX=True,
                scrollY=True,
                freeze_rows=1
            ):
                # Add columns
                for col in columns:
                    dpg.add_table_column(label=col)

                # Add rows (limit to first 500)
                for idx, row in dataframe.head(500).iterrows():
                    with dpg.table_row():
                        for col in columns:
                            value = str(row[col]) if pd.notna(row[col]) else ""
                            # Truncate long values
                            if len(value) > 50:
                                value = value[:47] + "..."
                            dpg.add_text(value)

    def set_controls_state(self, state: ProcessingState) -> None:
        """Update control buttons based on processing state."""
        if state == ProcessingState.IDLE:
            dpg.show_item(self.start_btn_id)
            dpg.enable_item(self.start_btn_id)
            dpg.hide_item(self.pause_btn_id)
            dpg.hide_item(self.resume_btn_id)
            dpg.hide_item(self.cancel_btn_id)

        elif state == ProcessingState.PROCESSING:
            dpg.hide_item(self.start_btn_id)
            dpg.show_item(self.pause_btn_id)
            dpg.hide_item(self.resume_btn_id)
            dpg.show_item(self.cancel_btn_id)

        elif state == ProcessingState.PAUSED:
            dpg.hide_item(self.start_btn_id)
            dpg.hide_item(self.pause_btn_id)
            dpg.show_item(self.resume_btn_id)
            dpg.show_item(self.cancel_btn_id)

        elif state in [ProcessingState.COMPLETED, ProcessingState.ERROR, ProcessingState.CANCELLED]:
            dpg.show_item(self.start_btn_id)
            dpg.enable_item(self.start_btn_id)
            dpg.hide_item(self.pause_btn_id)
            dpg.hide_item(self.resume_btn_id)
            dpg.hide_item(self.cancel_btn_id)

    def add_console_message(self, message: str) -> None:
        """Add message to console."""
        if self.console_panel:
            self.console_panel.add_message(message)

    def show(self) -> None:
        """Show the project view."""
        if dpg.does_item_exist(self.container_id):
            dpg.show_item(self.container_id)

    def hide(self) -> None:
        """Hide the project view."""
        if dpg.does_item_exist(self.container_id):
            dpg.hide_item(self.container_id)

    def cleanup(self) -> None:
        """Clean up resources."""
        if dpg.does_item_exist(self.container_id):
            dpg.delete_item(self.container_id)
