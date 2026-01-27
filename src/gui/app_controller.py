"""
Application controller - manages navigation between screens.

Coordinates the start screen, new project wizard, and project view.
Follows MVP pattern: observes NavigationState model and updates views accordingly.
"""

import dearpygui.dearpygui as dpg
from typing import Optional

from gui.views.start_screen import StartScreen
from gui.views.new_project_wizard import NewProjectWizard
from gui.views.project_view import ProjectView
from gui.views.add_urls_dialog import AddUrlsDialog
from gui.views.interrupted_run_dialog import InterruptedRunDialog
from presenters.start_screen_presenter import StartScreenPresenter
from presenters.new_project_presenter import NewProjectPresenter
from presenters.project_presenter import ProjectPresenter
from services.project_service import ProjectService
from services.run_service import RunService
from models.project_state import ProjectState
from models.navigation_state import NavigationState, Screen


class AppController:
    """
    Application-level presenter managing screen navigation.

    Responsibilities:
    - Own the NavigationState model
    - Observe navigation changes and update views
    - Coordinate between screen-level presenters
    - Manage view lifecycle

    Screens:
    - START: Initial screen with New/Open Project buttons
    - NEW_PROJECT: Project creation wizard
    - PROJECT: Main project view when a project is open
    """

    def __init__(self, main_window_id: str):
        self.main_window_id = main_window_id

        # Navigation state model
        self.navigation_state = NavigationState()

        # Services (shared across presenters)
        self.project_service = ProjectService()
        self.run_service = RunService()

        # Views
        self.start_screen: Optional[StartScreen] = None
        self.new_project_wizard: Optional[NewProjectWizard] = None
        self.project_view: Optional[ProjectView] = None
        self.add_urls_dialog: Optional[AddUrlsDialog] = None
        self.interrupted_run_dialog: Optional[InterruptedRunDialog] = None

        # Presenters
        self.start_screen_presenter: Optional[StartScreenPresenter] = None
        self.new_project_presenter: Optional[NewProjectPresenter] = None
        self.project_presenter: Optional[ProjectPresenter] = None

        # Current project (when in PROJECT screen)
        self.current_project: Optional[ProjectState] = None

    def setup(self) -> None:
        """Setup all views, presenters, and navigation observer."""
        self._setup_views()
        self._setup_presenters()
        self._setup_navigation()

    def _setup_views(self) -> None:
        """Create and setup all view instances."""
        # Create views
        self.start_screen = StartScreen()
        self.new_project_wizard = NewProjectWizard()
        self.project_view = ProjectView()
        self.add_urls_dialog = AddUrlsDialog()
        self.interrupted_run_dialog = InterruptedRunDialog()

        # Setup view UIs (all as children of main window)
        self.start_screen.setup_ui(self.main_window_id)
        self.new_project_wizard.setup_ui(self.main_window_id)
        self.project_view.setup_ui(self.main_window_id)
        self.add_urls_dialog.setup_ui()
        self.interrupted_run_dialog.setup_ui()

        # Initially hide all except start screen
        self.new_project_wizard.hide()
        self.project_view.hide()

    def _setup_presenters(self) -> None:
        """Create presenters and wire up callbacks."""
        # Start screen presenter
        self.start_screen_presenter = StartScreenPresenter(
            view=self.start_screen,
            project_service=self.project_service
        )
        self.start_screen_presenter.set_navigation_callbacks(
            on_show_new_project_wizard=self._on_show_new_project,
            on_project_opened=self._on_project_opened
        )

        # New project presenter
        self.new_project_presenter = NewProjectPresenter(
            view=self.new_project_wizard,
            project_service=self.project_service
        )
        self.new_project_presenter.set_navigation_callbacks(
            on_project_created=self._on_project_created,
            on_cancelled=self._on_new_project_cancelled
        )

        # Project presenter
        self.project_presenter = ProjectPresenter(
            view=self.project_view,
            add_urls_dialog=self.add_urls_dialog,
            interrupted_run_dialog=self.interrupted_run_dialog,
            project_service=self.project_service,
            run_service=self.run_service
        )
        self.project_presenter.set_navigation_callbacks(
            on_close_project=self._on_close_project
        )

    def _setup_navigation(self) -> None:
        """Setup navigation state observer."""
        self.navigation_state.add_observer(self._on_navigation_changed)

    def _on_navigation_changed(self, previous: Screen, current: Screen) -> None:
        """
        Handle navigation state changes.

        This is the single point where view visibility is managed.
        Called by NavigationState when navigate_to() is invoked.

        Args:
            previous: The screen we're leaving
            current: The screen we're navigating to
        """
        # Hide all screens
        self.start_screen.hide()
        self.new_project_wizard.hide()
        self.project_view.hide()

        # Show the target screen (using presenter for screens that need state management)
        if current == Screen.START:
            self.start_screen.show()
        elif current == Screen.NEW_PROJECT:
            # Use presenter to handle state reset and show
            self.new_project_presenter.show()
        elif current == Screen.PROJECT:
            self.project_view.show()

        print(f"Navigation: {previous.value} -> {current.value}")

    # === Navigation action handlers ===
    # These are called by presenters and translate to navigation state changes

    def _on_show_new_project(self) -> None:
        """Handle request to show new project wizard."""
        self.navigation_state.navigate_to(Screen.NEW_PROJECT)

    def _on_new_project_cancelled(self) -> None:
        """Handle cancellation of new project wizard."""
        self.navigation_state.navigate_to(Screen.START)

    def _on_project_created(self, project_state: ProjectState) -> None:
        """Handle successful project creation."""
        self._open_project(project_state)

    def _on_project_opened(self, project_state: ProjectState) -> None:
        """Handle opening an existing project."""
        self._open_project(project_state)

    def _on_close_project(self) -> None:
        """Handle closing the current project."""
        self.current_project = None
        self.navigation_state.navigate_to(Screen.START)
        print("Closed project")

    def _open_project(self, project_state: ProjectState) -> None:
        """
        Open a project and navigate to project view.

        Args:
            project_state: The project to open
        """
        self.current_project = project_state

        # Navigate to project screen (this will show project_view)
        self.navigation_state.navigate_to(Screen.PROJECT)

        # Initialize project presenter with the project data
        self.project_presenter.initialize(project_state)

        print(f"Opened project: {project_state.name}")

    def handle_viewport_resize(self) -> None:
        """Handle viewport resize - re-center visible cards."""
        # Re-center the card for the current screen
        if self.navigation_state.current_screen == Screen.START:
            if self.start_screen:
                self.start_screen._center_card()
        elif self.navigation_state.current_screen == Screen.NEW_PROJECT:
            if self.new_project_wizard:
                self.new_project_wizard._center_card()
        # PROJECT screen doesn't use centered card layout

    def cleanup(self) -> None:
        """Clean up all resources."""
        # Remove navigation observer
        self.navigation_state.remove_observer(self._on_navigation_changed)

        # Cleanup presenters
        if self.project_presenter:
            self.project_presenter.cleanup()

        # Cleanup views
        if self.start_screen:
            self.start_screen.cleanup()

        if self.new_project_wizard:
            self.new_project_wizard.cleanup()

        if self.project_view:
            self.project_view.cleanup()
