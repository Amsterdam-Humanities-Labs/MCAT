"""
Presenter for the start screen.

Handles navigation to new project wizard or opening existing projects.
"""

from pathlib import Path
from typing import Callable, Optional

from gui.views.start_screen import StartScreen
from services.project_service import ProjectService
from models.project_state import ProjectState


class StartScreenPresenter:
    """
    Presenter for the start screen view.

    Responsibilities:
    - Handle "New Project" click -> show wizard
    - Handle "Open Project" click -> folder dialog, then load project
    """

    def __init__(
        self,
        view: StartScreen,
        project_service: ProjectService
    ):
        self.view = view
        self.project_service = project_service

        # Callbacks to app controller
        self._on_show_new_project_wizard: Optional[Callable] = None
        self._on_project_opened: Optional[Callable[[ProjectState], None]] = None

        # Wire up view callbacks
        self.view.set_callbacks(
            on_new_project=self._handle_new_project,
            on_open_project=self._handle_open_project
        )
        self.view.set_presenter(self)

    def set_navigation_callbacks(
        self,
        on_show_new_project_wizard: Callable,
        on_project_opened: Callable[[ProjectState], None]
    ) -> None:
        """
        Set callbacks for navigation.

        Args:
            on_show_new_project_wizard: Called to show new project wizard
            on_project_opened: Called when a project is successfully opened
        """
        self._on_show_new_project_wizard = on_show_new_project_wizard
        self._on_project_opened = on_project_opened

    def _handle_new_project(self) -> None:
        """Handle New Project button click."""
        if self._on_show_new_project_wizard:
            self._on_show_new_project_wizard()

    def _handle_open_project(self) -> None:
        """Handle Open Project button click."""
        import dearpygui.dearpygui as dpg

        def folder_callback(sender, app_data):
            if app_data.get('file_path_name'):
                folder_path = Path(app_data['file_path_name'])
                self._open_project(folder_path)

        dpg.add_file_dialog(
            directory_selector=True,
            show=True,
            callback=folder_callback,
            width=600,
            height=400
        )

    def _open_project(self, project_path: Path) -> None:
        """
        Open a project from the given path.

        Args:
            project_path: Path to project folder
        """
        # Validate project structure
        is_valid, error = self.project_service.validate_project_structure(project_path)
        if not is_valid:
            print(f"Invalid project: {error}")
            return

        try:
            project_state = self.project_service.open_project(project_path)
            print(f"Opened project: {project_state.name}")

            if self._on_project_opened:
                self._on_project_opened(project_state)

        except Exception as e:
            print(f"Error opening project: {e}")
