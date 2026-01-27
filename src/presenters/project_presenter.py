"""
Presenter for the project view.

Handles run lifecycle, progress updates, and project actions.
Owns state for dialogs following MVP pattern.
"""

import dearpygui.dearpygui as dpg
from pathlib import Path
from typing import Callable, Optional

from events import dispatcher, ProcessingEvents

from gui.views.project_view import ProjectView
from gui.views.add_urls_dialog import AddUrlsDialog
from gui.views.interrupted_run_dialog import InterruptedRunDialog
from services.project_service import ProjectService
from services.run_service import RunService
from services.processing_service import ProcessingService
from models.project_state import ProjectState
from models.project_models import RunConfig
from models.processing_models import ProcessingState
from models.wizard_state import AddUrlsDialogState, InterruptedRunDialogState


class ProjectPresenter:
    """
    Presenter for the project view.

    Responsibilities:
    - Initialize view with project data
    - Handle run lifecycle (start, pause, resume, cancel)
    - Handle progress updates from ProcessingService
    - Handle URL imports (owns AddUrlsDialogState)
    - Detect and handle interrupted runs (owns InterruptedRunDialogState)
    """

    def __init__(
        self,
        view: ProjectView,
        add_urls_dialog: AddUrlsDialog,
        interrupted_run_dialog: InterruptedRunDialog,
        project_service: ProjectService,
        run_service: RunService
    ):
        self.view = view
        self.add_urls_dialog = add_urls_dialog
        self.interrupted_run_dialog = interrupted_run_dialog
        self.project_service = project_service
        self.run_service = run_service

        # Project state
        self.project_state: Optional[ProjectState] = None
        self.processing_service: Optional[ProcessingService] = None
        self.current_run: Optional[RunConfig] = None

        # Dialog state models (owned by presenter)
        self.add_urls_state = AddUrlsDialogState()
        self.interrupted_run_state = InterruptedRunDialogState()

        # Callbacks to app controller
        self._on_close_project: Optional[Callable] = None

        # Wire up view callbacks
        self.view.set_callbacks(
            on_start_run=self._handle_start_run,
            on_pause=self._handle_pause,
            on_resume=self._handle_resume,
            on_cancel=self._handle_cancel,
            on_add_urls=self._handle_add_urls,
            on_close_project=self._handle_close_project
        )
        self.view.set_presenter(self)

        # Wire up add URLs dialog (presenter handles all logic)
        self.add_urls_dialog.set_callbacks(
            on_browse_csv=self._handle_add_urls_browse,
            on_import=self._handle_add_urls_import,
            on_cancel=self._handle_add_urls_cancel
        )

        # Wire up interrupted run dialog
        self.interrupted_run_dialog.set_callbacks(
            on_resume=self._handle_interrupted_resume,
            on_start_new=self._handle_interrupted_start_new
        )

    def set_navigation_callbacks(
        self,
        on_close_project: Callable
    ) -> None:
        """Set callbacks for navigation."""
        self._on_close_project = on_close_project

    def initialize(self, project_state: ProjectState) -> None:
        """
        Initialize presenter with project data.

        Args:
            project_state: The project to display
        """
        self.project_state = project_state

        # Create processing service for this project's platform
        self.processing_service = ProcessingService(platform=project_state.platform)

        # Subscribe to processing events
        self._subscribe_to_events()

        # Update view with project info
        url_count = self.project_service.get_url_count(project_state)
        self.view.show_project_info(
            name=project_state.name,
            platform=project_state.platform,
            url_count=url_count
        )

        # Show run history
        self.view.show_run_history(project_state.config.runs)

        # Load and display combined results if available
        if project_state.combined_csv_path.exists():
            import pandas as pd
            try:
                df = pd.read_csv(project_state.combined_csv_path)
                self.view.show_results(df)
            except Exception:
                pass

        # Check for interrupted run
        if project_state.has_interrupted_run:
            interrupted_run = project_state.interrupted_run
            processed = self.run_service.get_processed_count(project_state, interrupted_run)
            total = url_count

            # Update interrupted run dialog state
            self.interrupted_run_state.run = interrupted_run
            self.interrupted_run_state.processed_count = processed
            self.interrupted_run_state.total_count = total

            # Display dialog with state data
            self.interrupted_run_dialog.display_details(self.interrupted_run_state.details_text)
            self.interrupted_run_dialog.show()

    def _subscribe_to_events(self) -> None:
        """Subscribe to processing events."""
        dispatcher.connect(
            self._on_processing_progress,
            ProcessingEvents.PROGRESS,
            sender=self.processing_service
        )
        dispatcher.connect(
            self._on_processing_started,
            ProcessingEvents.STARTED,
            sender=self.processing_service
        )
        dispatcher.connect(
            self._on_processing_completed,
            ProcessingEvents.COMPLETED,
            sender=self.processing_service
        )
        dispatcher.connect(
            self._on_processing_cancelled,
            ProcessingEvents.CANCELLED,
            sender=self.processing_service
        )
        dispatcher.connect(
            self._on_processing_error,
            ProcessingEvents.ERROR,
            sender=self.processing_service
        )
        dispatcher.connect(
            self._on_processing_paused,
            ProcessingEvents.PAUSED,
            sender=self.processing_service
        )
        dispatcher.connect(
            self._on_processing_resumed,
            ProcessingEvents.RESUMED,
            sender=self.processing_service
        )

    def _unsubscribe_from_events(self) -> None:
        """Unsubscribe from processing events."""
        if self.processing_service:
            dispatcher.disconnect(
                self._on_processing_progress,
                ProcessingEvents.PROGRESS,
                sender=self.processing_service
            )
            dispatcher.disconnect(
                self._on_processing_started,
                ProcessingEvents.STARTED,
                sender=self.processing_service
            )
            dispatcher.disconnect(
                self._on_processing_completed,
                ProcessingEvents.COMPLETED,
                sender=self.processing_service
            )
            dispatcher.disconnect(
                self._on_processing_cancelled,
                ProcessingEvents.CANCELLED,
                sender=self.processing_service
            )
            dispatcher.disconnect(
                self._on_processing_error,
                ProcessingEvents.ERROR,
                sender=self.processing_service
            )
            dispatcher.disconnect(
                self._on_processing_paused,
                ProcessingEvents.PAUSED,
                sender=self.processing_service
            )
            dispatcher.disconnect(
                self._on_processing_resumed,
                ProcessingEvents.RESUMED,
                sender=self.processing_service
            )

    # === Run control handlers ===

    def _handle_start_run(self, screenshots_enabled: bool) -> None:
        """Handle Start Run button click."""
        if not self.project_state:
            return

        # Start a new run
        self.current_run = self.run_service.start_run(
            self.project_state,
            screenshots_enabled=screenshots_enabled
        )

        # Get all URLs
        urls = self.project_service.get_urls(self.project_state)

        # Start processing
        self._start_processing(urls, screenshots_enabled)

    def _handle_interrupted_resume(self) -> None:
        """Handle resume interrupted run."""
        if not self.project_state or not self.interrupted_run_state.run:
            return

        # Resume the run using state
        self.current_run, remaining_urls = self.run_service.resume_run(
            self.project_state,
            self.interrupted_run_state.run
        )

        print(f"Resuming run {self.current_run.id} with {len(remaining_urls)} remaining URLs")

        # Clear interrupted run state
        self.interrupted_run_state.reset()

        # Start processing remaining URLs
        self._start_processing(remaining_urls, self.current_run.screenshots_enabled)

    def _handle_interrupted_start_new(self) -> None:
        """Handle start new (abandon interrupted)."""
        if not self.project_state or not self.interrupted_run_state.run:
            return

        # Abandon the interrupted run using state
        self.run_service.abandon_run(self.project_state, self.interrupted_run_state.run)
        print(f"Abandoned run {self.interrupted_run_state.run.id}")

        # Clear interrupted run state
        self.interrupted_run_state.reset()

        # Update run history in view
        self.view.show_run_history(self.project_state.config.runs)

    def _start_processing(self, urls: list, screenshots_enabled: bool) -> None:
        """Start processing URLs."""
        if not self.project_state or not self.current_run:
            return

        # Create column mapping
        from models.file_models import ColumnMapping
        column_mapping = ColumnMapping(
            post_column=self.project_state.url_column,
            preserve_columns=self.project_state.preserve_columns
        )

        # Get run output path
        run_path = self.project_state.get_run_path(self.current_run.id)

        # Create processing job
        from models.processing_models import ProcessingJob
        from models.file_models import FileInfo

        file_info = FileInfo(
            path=str(self.project_state.urls_csv_path),
            valid=True,
            row_count=len(urls)
        )

        job = ProcessingJob(
            file_info=file_info,
            column_mapping=column_mapping,
            platform=self.project_state.platform,
            output_folder=str(run_path),
            save_screenshots=screenshots_enabled
        )

        # Start processing
        self.processing_service.start_processing(job, urls=urls)

    def _handle_pause(self) -> None:
        """Handle Pause button click."""
        if self.processing_service:
            self.processing_service.pause_processing()

    def _handle_resume(self) -> None:
        """Handle Resume button click."""
        if self.processing_service:
            self.processing_service.resume_processing()

    def _handle_cancel(self) -> None:
        """Handle Cancel button click."""
        if self.processing_service:
            self.processing_service.cancel_processing()

    # === Processing event handlers ===

    def _on_processing_started(self, sender=None, **kwargs) -> None:
        """Handle processing started event."""
        self.view.set_controls_state(ProcessingState.PROCESSING)

    def _on_processing_progress(self, sender=None, **kwargs) -> None:
        """Handle progress update event."""
        stats = kwargs.get('stats', {})
        total = kwargs.get('total', 0)
        current = kwargs.get('current', 0)
        action = kwargs.get('action', '')

        self.view.show_progress(stats, total, current, action)

    def _on_processing_completed(self, sender=None, **kwargs) -> None:
        """Handle processing completed event."""
        self.view.set_controls_state(ProcessingState.COMPLETED)
        self.view.clear_progress()

        # Complete the run
        if self.current_run and self.project_state:
            self.run_service.complete_run(self.project_state, self.current_run)

            # Refresh run history
            self.view.show_run_history(self.project_state.config.runs)

            # Refresh results
            if self.project_state.combined_csv_path.exists():
                import pandas as pd
                try:
                    df = pd.read_csv(self.project_state.combined_csv_path)
                    self.view.show_results(df)
                except Exception:
                    pass

        self.current_run = None

    def _on_processing_cancelled(self, sender=None, **kwargs) -> None:
        """Handle processing cancelled event."""
        self.view.set_controls_state(ProcessingState.IDLE)
        self.view.clear_progress()

        # Run stays in_progress for later resume
        self.current_run = None

        # Refresh run history
        if self.project_state:
            self.view.show_run_history(self.project_state.config.runs)

    def _on_processing_error(self, sender=None, **kwargs) -> None:
        """Handle processing error event."""
        error_message = kwargs.get('error_message', 'Unknown error')
        print(f"Processing error: {error_message}")

        self.view.set_controls_state(ProcessingState.ERROR)
        self.current_run = None

    def _on_processing_paused(self, sender=None, **kwargs) -> None:
        """Handle processing paused event."""
        self.view.set_controls_state(ProcessingState.PAUSED)

    def _on_processing_resumed(self, sender=None, **kwargs) -> None:
        """Handle processing resumed event."""
        self.view.set_controls_state(ProcessingState.PROCESSING)

    # === Add URLs dialog handlers ===

    def _handle_add_urls(self) -> None:
        """Handle Add URLs button click - show dialog."""
        self.add_urls_state.reset()
        self.add_urls_dialog.reset()
        self.add_urls_dialog.show()

    def _handle_add_urls_browse(self) -> None:
        """Handle browse CSV in add URLs dialog."""
        def callback(sender, app_data):
            selections = app_data.get('selections', {})
            if selections:
                file_path = list(selections.values())[0]
                self.add_urls_state.selected_csv = Path(file_path)

                # Update view
                self.add_urls_dialog.display_csv_path(str(self.add_urls_state.selected_csv))

                # Preview import
                self._preview_url_import()

        dpg.add_file_dialog(
            directory_selector=False,
            show=True,
            callback=callback,
            width=600,
            height=400
        )

    def _preview_url_import(self) -> None:
        """Preview URL import and update dialog."""
        if not self.project_state or not self.add_urls_state.selected_csv:
            return

        try:
            # Get import preview from service
            self.add_urls_state.import_result = self.project_service.preview_url_import(
                self.project_state,
                self.add_urls_state.selected_csv
            )

            result = self.add_urls_state.import_result

            if result.has_error:
                self.add_urls_state.has_error = True
                self.add_urls_state.error_message = result.error_message
                self.add_urls_dialog.display_error(result.error_message)
                self.add_urls_dialog.display_preview("")
                self.add_urls_dialog.set_import_enabled(False)
            else:
                self.add_urls_state.has_error = False
                self.add_urls_dialog.hide_error()
                self.add_urls_dialog.display_preview(result.summary)

                if result.is_valid:
                    self.add_urls_dialog.set_import_enabled(True)
                else:
                    self.add_urls_dialog.set_import_enabled(False)
                    if result.all_duplicates:
                        self.add_urls_dialog.display_preview(
                            "All URLs in this file already exist in the project."
                        )

        except Exception as e:
            self.add_urls_state.has_error = True
            self.add_urls_state.error_message = str(e)
            self.add_urls_dialog.display_error(str(e))
            self.add_urls_dialog.set_import_enabled(False)

    def _handle_add_urls_import(self) -> None:
        """Handle import confirmation in add URLs dialog."""
        if not self.project_state or not self.add_urls_state.can_import():
            return

        try:
            added = self.project_service.confirm_url_import(
                self.project_state,
                self.add_urls_state.import_result
            )

            print(f"Added {added} URLs to project")

            # Refresh project info
            url_count = self.project_service.get_url_count(self.project_state)
            self.view.show_project_info(
                name=self.project_state.name,
                platform=self.project_state.platform,
                url_count=url_count
            )

            # Clear state and hide dialog
            self.add_urls_state.reset()
            self.add_urls_dialog.hide()

        except Exception as e:
            self.add_urls_state.has_error = True
            self.add_urls_state.error_message = str(e)
            self.add_urls_dialog.display_error(str(e))

    def _handle_add_urls_cancel(self) -> None:
        """Handle cancel in add URLs dialog."""
        self.add_urls_state.reset()

    # === Project actions ===

    def _handle_close_project(self) -> None:
        """Handle Close Project button click."""
        # Unsubscribe from events
        self._unsubscribe_from_events()

        # Save project state
        if self.project_state:
            self.project_service.save_project(self.project_state)

        self.project_state = None
        self.processing_service = None

        if self._on_close_project:
            self._on_close_project()

    def cleanup(self) -> None:
        """Clean up resources."""
        self._unsubscribe_from_events()
