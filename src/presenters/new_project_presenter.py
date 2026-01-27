"""
Presenter for the new project wizard.

Owns wizard state and handles all business logic for project creation.
Follows MVP pattern where presenter owns state and view is passive.
"""

import dearpygui.dearpygui as dpg
from pathlib import Path
from typing import Callable, List, Optional
import pandas as pd

from gui.views.new_project_wizard import NewProjectWizard
from services.project_service import ProjectService
from models.project_state import ProjectState
from models.wizard_state import NewProjectWizardState


class NewProjectPresenter:
    """
    Presenter for the new project wizard.

    Responsibilities:
    - Own and manage wizard state (NewProjectWizardState)
    - Handle all user interactions from view
    - Validate inputs at each step
    - Create project via ProjectService
    - Update view to reflect state changes
    """

    def __init__(
        self,
        view: NewProjectWizard,
        project_service: ProjectService
    ):
        self.view = view
        self.project_service = project_service

        # State model (owned by presenter)
        self.state = NewProjectWizardState()

        # Callbacks to app controller
        self._on_project_created: Optional[Callable[[ProjectState], None]] = None
        self._on_cancelled: Optional[Callable[[], None]] = None

        # Wire up view callbacks
        self.view.set_callbacks(
            on_name_changed=self._handle_name_changed,
            on_platform_changed=self._handle_platform_changed,
            on_browse_location=self._handle_browse_location,
            on_browse_csv=self._handle_browse_csv,
            on_url_column_changed=self._handle_url_column_changed,
            on_preserve_column_toggled=self._handle_preserve_column_toggled,
            on_next=self._handle_next,
            on_back=self._handle_back,
            on_cancel=self._handle_cancel
        )

    def set_navigation_callbacks(
        self,
        on_project_created: Callable[[ProjectState], None],
        on_cancelled: Callable[[], None]
    ) -> None:
        """Set callbacks for navigation to app controller."""
        self._on_project_created = on_project_created
        self._on_cancelled = on_cancelled

    def show(self) -> None:
        """Show the wizard and reset state."""
        self.state.reset()
        self._sync_view_with_state()
        self.view.show()

    def hide(self) -> None:
        """Hide the wizard."""
        self.view.hide()

    # === State change handlers ===

    def _handle_name_changed(self, name: str) -> None:
        """Handle project name change."""
        self.state.name = name.strip()

    def _handle_platform_changed(self, platform: str) -> None:
        """Handle platform selection change."""
        self.state.platform = platform

    def _handle_browse_location(self) -> None:
        """Handle browse location button click."""
        def callback(sender, app_data):
            if app_data.get('file_path_name'):
                self.state.selected_location = Path(app_data['file_path_name'])
                self.view.display_location(str(self.state.selected_location))

        dpg.add_file_dialog(
            directory_selector=True,
            show=True,
            callback=callback,
            width=600,
            height=400
        )

    def _handle_browse_csv(self) -> None:
        """Handle browse CSV button click."""
        def callback(sender, app_data):
            selections = app_data.get('selections', {})
            if selections:
                file_path = list(selections.values())[0]
                self.state.selected_csv = Path(file_path)
                self.view.display_csv_path(str(self.state.selected_csv))
                self._load_csv_columns()

        default_path = str(self.state.selected_location) if self.state.selected_location else ""
        dpg.add_file_dialog(
            directory_selector=False,
            show=True,
            callback=callback,
            width=600,
            height=400,
            default_path=default_path
        )

    def _handle_url_column_changed(self, column: str) -> None:
        """Handle URL column selection change."""
        self.state.url_column = column
        # Refresh preserve columns display (exclude URL column)
        self.view.display_preserve_columns(
            self.state.csv_columns,
            self.state.url_column,
            self.state.preserve_columns
        )

    def _handle_preserve_column_toggled(self, column: str, is_checked: bool) -> None:
        """Handle preserve column checkbox toggle."""
        if is_checked and column not in self.state.preserve_columns:
            self.state.preserve_columns.append(column)
        elif not is_checked and column in self.state.preserve_columns:
            self.state.preserve_columns.remove(column)

    def _handle_next(self) -> None:
        """Handle next button click."""
        if self.state.current_step == 1:
            if self._validate_step1():
                self.state.current_step = 2
                self._sync_view_with_state()
        elif self.state.current_step == 2:
            if self._validate_step2():
                self._create_project()

    def _handle_back(self) -> None:
        """Handle back button click."""
        if self.state.current_step == 2:
            self.state.current_step = 1
            self.state.has_error = False
            self.state.error_message = ""
            self._sync_view_with_state()

    def _handle_cancel(self) -> None:
        """Handle cancel button click."""
        self.view.hide()
        if self._on_cancelled:
            self._on_cancelled()

    # === Internal methods ===

    def _load_csv_columns(self) -> None:
        """Load columns from selected CSV file."""
        if not self.state.selected_csv or not self.state.selected_csv.exists():
            return

        try:
            df = pd.read_csv(self.state.selected_csv, nrows=0)
            self.state.csv_columns = list(df.columns)

            # Auto-select URL column
            self.state.url_column = self._guess_url_column(self.state.csv_columns)

            # Update view
            self.view.display_columns(self.state.csv_columns, self.state.url_column)

        except Exception as e:
            self._show_error(f"Error reading CSV: {e}")

    def _guess_url_column(self, columns: List[str]) -> str:
        """Guess which column contains URLs."""
        url_keywords = ['url', 'link', 'video', 'post', 'href']
        for col in columns:
            if any(kw in col.lower() for kw in url_keywords):
                return col
        return columns[0] if columns else ""

    def _validate_step1(self) -> bool:
        """Validate step 1 inputs."""
        # Read current values from view (in case callbacks didn't fire)
        self.state.name = self.view.get_name().strip()
        self.state.platform = self.view.get_platform()

        if not self.state.name:
            self._show_error("Please enter a project name")
            return False

        if not self.state.selected_location:
            self._show_error("Please select a project location")
            return False

        if not self.state.selected_csv:
            self._show_error("Please select a source CSV file")
            return False

        if not self.state.selected_csv.exists():
            self._show_error("Selected CSV file does not exist")
            return False

        # Check if project folder would already exist
        project_path = self.state.selected_location / self.state.name
        if project_path.exists():
            self._show_error(f"Project folder already exists: {project_path}")
            return False

        self._hide_error()
        return True

    def _validate_step2(self) -> bool:
        """Validate step 2 inputs."""
        # Read current value from view
        self.state.url_column = self.view.get_url_column()

        if not self.state.url_column:
            self._show_error("Please select a URL column")
            return False

        self._hide_error()
        return True

    def _create_project(self) -> None:
        """Create the project using current state."""
        try:
            project_state = self.project_service.create_project(
                name=self.state.name,
                platform=self.state.platform,
                location=self.state.selected_location,
                source_csv=self.state.selected_csv,
                url_column=self.state.url_column,
                preserve_columns=self.state.preserve_columns
            )

            print(f"Created project: {project_state.name}")
            print(f"Project path: {project_state.project_path}")
            print(f"URLs: {self.project_service.get_url_count(project_state)}")

            self.view.hide()

            if self._on_project_created:
                self._on_project_created(project_state)

        except FileExistsError as e:
            self._show_error(str(e))
        except ValueError as e:
            self._show_error(str(e))
        except Exception as e:
            self._show_error(f"Error creating project: {e}")

    def _sync_view_with_state(self) -> None:
        """Sync view display with current state."""
        # Display current step
        self.view.display_step(self.state.current_step)

        # Display step 1 data
        self.view.display_name(self.state.name)
        self.view.display_platform(self.state.platform)

        if self.state.selected_location:
            self.view.display_location(str(self.state.selected_location))
        else:
            self.view.display_location("")

        if self.state.selected_csv:
            self.view.display_csv_path(str(self.state.selected_csv))
        else:
            self.view.display_csv_path("")

        # Display step 2 data (if we have columns)
        if self.state.csv_columns:
            self.view.display_columns(self.state.csv_columns, self.state.url_column)
            self.view.display_preserve_columns(
                self.state.csv_columns,
                self.state.url_column,
                self.state.preserve_columns
            )

        # Display error state
        if self.state.has_error:
            self.view.display_error(self.state.error_message)
        else:
            self.view.hide_error()

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.state.has_error = True
        self.state.error_message = message
        self.view.display_error(message)

    def _hide_error(self) -> None:
        """Hide error message."""
        self.state.has_error = False
        self.state.error_message = ""
        self.view.hide_error()
