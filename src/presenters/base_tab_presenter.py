"""
Base tab presenter implementing common workflow for all platform tabs.

This presenter handles the shared business logic coordination between 
UI components and services, following the MVP pattern.
"""

from typing import Optional, Dict, Any
from abc import ABC
from pathlib import Path

from models.file_models import FileInfo, ColumnMapping, ValidationResult
from models.processing_models import ProcessingJob, ProcessingStatus, ProcessingState
from services.csv_service import CSVService
from services.processing_service import ProcessingService
from events import dispatcher, ProcessingEvents


class BaseTabPresenter:
    """Base presenter for all platform tabs - handles common workflow."""
    
    def __init__(self, view, platform: str):
        """
        Initialize base tab presenter.
        
        Args:
            view: The view component this presenter coordinates
            platform: Platform name (e.g., 'youtube', 'facebook', 'twitter')
        """
        self.view = view
        self.platform = platform

        # Shared services (same for all platforms)
        self.csv_service = CSVService()
        self.processing_service = ProcessingService()

        # Current state
        self.current_file: Optional[FileInfo] = None
        self.current_column_mapping = ColumnMapping()
        self.output_folder: Optional[Path] = None
        
        # Subscribe to processing events
        self._subscribe_to_events()
    
    def initialize(self):
        """Initialize presenter and setup view callbacks."""
        # The view will call presenter methods directly via UI callbacks
        # No additional setup needed in base implementation
        pass

    def cleanup(self):
        """Cleanup presenter resources."""
        # Unsubscribe from events to prevent memory leaks
        self._unsubscribe_from_events()

        if self.processing_service:
            self.processing_service.cleanup()
    
    # Common workflow methods (shared across all tabs)
    
    def handle_file_selected(self, file_path: str):
        """
        Handle file selection workflow - same for all platforms.

        Args:
            file_path: Path to the selected CSV file
        """
        # Use CSV service to load and validate file
        file_info = self.csv_service.load_file(file_path)
        self.current_file = file_info

        if file_info.valid:
            # Auto-determine output folder
            csv_path = Path(file_path)
            csv_dir = csv_path.parent
            csv_stem = csv_path.stem
            self.output_folder = csv_dir / f"{csv_stem}_results"

            # Log to console (captured by ConsoleLogger)
            print(f"✅ Loaded file: {file_info.filename} ({file_info.row_count} rows, {len(file_info.columns)} columns)")
            print(f"📁 Results will be saved to: {self.output_folder}")

            # Update view with success
            self.view.show_file_success(file_info)
            self.view.populate_columns(file_info.columns)

            # Show output folder in view
            if hasattr(self.view, 'show_output_folder'):
                self.view.show_output_folder(str(self.output_folder))

            # Platform-specific column suggestions
            self._suggest_columns(file_info)

            # Reset column mapping for new file
            self.current_column_mapping = ColumnMapping()

            # Trigger initial validation
            self._validate_current_state()
        else:
            # Update view with error
            self.view.show_file_error(file_info.error_message)
            self.current_file = None
            self.output_folder = None
    
    def handle_column_mapping_changed(self, post_column: str, preserve_columns: list):
        """
        Handle column mapping changes.

        Args:
            post_column: Selected post/URL column
            preserve_columns: List of columns to preserve in output
        """
        self.current_column_mapping = ColumnMapping(
            post_column=post_column,
            preserve_columns=preserve_columns
        )

        # Log to console (captured by ConsoleLogger)
        url_part = f"'{post_column}'" if post_column else "None"
        if preserve_columns:
            cols_str = ", ".join(preserve_columns)
            print(f"📋 Column mapping: URL = {url_part}, Preserve = [{cols_str}]")
        else:
            print(f"📋 Column mapping: URL = {url_part}, Preserve = []")

        # Re-validate with new mapping
        self._validate_current_state()
    
    def handle_start_processing(self):
        """
        Handle start processing request - same logic, different platform.
        """
        if not self._validate_processing_request():
            return

        # Get screenshot preference from view
        save_screenshots = False
        if hasattr(self.view, 'get_screenshot_enabled'):
            save_screenshots = self.view.get_screenshot_enabled()

        # Create output folder
        if self.output_folder:
            self.output_folder.mkdir(parents=True, exist_ok=True)

        # Create processing job
        job = ProcessingJob(
            file_info=self.current_file,
            column_mapping=self.current_column_mapping,
            platform=self.platform,
            output_folder=str(self.output_folder) if self.output_folder else "",
            save_screenshots=save_screenshots
        )

        # Log to console (captured by ConsoleLogger)
        print(f"🚀 Started processing {job.file_info.row_count} URLs")
        if save_screenshots:
            print(f"📷 Screenshots enabled - saving to {self.output_folder}/screenshots/")

        # Start processing using service
        # Events will handle view updates automatically
        self.processing_service.start_processing(job)
    
    def handle_pause_processing(self):
        """Handle pause processing request."""
        # Events will handle view updates automatically
        self.processing_service.pause_processing()
    
    def handle_resume_processing(self):
        """Handle resume processing request.""" 
        # Events will handle view updates automatically
        self.processing_service.resume_processing()
    
    def handle_cancel_processing(self):
        """Handle cancel processing request."""
        # Events will handle view updates automatically
        self.processing_service.cancel_processing()

    def handle_output_folder_changed(self, folder_path: str):
        """
        Handle output folder change from dropdown.

        Args:
            folder_path: Selected output folder path
        """
        from pathlib import Path
        self.output_folder = Path(folder_path)
        print(f"📁 Output folder changed to: {self.output_folder}")

    def get_current_file(self) -> Optional[FileInfo]:
        """Get the currently loaded file info."""
        return self.current_file
    
    def get_current_column_mapping(self) -> ColumnMapping:
        """Get the current column mapping."""
        return self.current_column_mapping
    
    def is_processing(self) -> bool:
        """Check if currently processing."""
        return self.processing_service.is_processing()
    
    def get_processing_results(self):
        """Get processing results if available."""
        return self.processing_service.get_results()
    
    # Internal methods
    
    def _subscribe_to_events(self):
        """Subscribe to processing events from services."""
        # Subscribe to events from our specific processing service instance
        dispatcher.connect(self._handle_progress_update, ProcessingEvents.PROGRESS, sender=self.processing_service)
        dispatcher.connect(self._handle_processing_complete, ProcessingEvents.COMPLETED, sender=self.processing_service)
        dispatcher.connect(self._handle_processing_error, ProcessingEvents.ERROR, sender=self.processing_service)
        dispatcher.connect(self._handle_processing_started, ProcessingEvents.STARTED, sender=self.processing_service)
        dispatcher.connect(self._handle_processing_paused, ProcessingEvents.PAUSED, sender=self.processing_service)
        dispatcher.connect(self._handle_processing_resumed, ProcessingEvents.RESUMED, sender=self.processing_service)
        dispatcher.connect(self._handle_processing_cancelled, ProcessingEvents.CANCELLED, sender=self.processing_service)

        # Subscribe to global events (from any platform) to update button state
        dispatcher.connect(self._handle_global_processing_changed, ProcessingEvents.STARTED, sender=dispatcher.Any)
        dispatcher.connect(self._handle_global_processing_changed, ProcessingEvents.COMPLETED, sender=dispatcher.Any)
        dispatcher.connect(self._handle_global_processing_changed, ProcessingEvents.CANCELLED, sender=dispatcher.Any)
        dispatcher.connect(self._handle_global_processing_changed, ProcessingEvents.ERROR, sender=dispatcher.Any)
    
    def _unsubscribe_from_events(self):
        """Unsubscribe from processing events to prevent memory leaks."""
        dispatcher.disconnect(self._handle_progress_update, ProcessingEvents.PROGRESS, sender=self.processing_service)
        dispatcher.disconnect(self._handle_processing_complete, ProcessingEvents.COMPLETED, sender=self.processing_service)
        dispatcher.disconnect(self._handle_processing_error, ProcessingEvents.ERROR, sender=self.processing_service)
        dispatcher.disconnect(self._handle_processing_started, ProcessingEvents.STARTED, sender=self.processing_service)
        dispatcher.disconnect(self._handle_processing_paused, ProcessingEvents.PAUSED, sender=self.processing_service)
        dispatcher.disconnect(self._handle_processing_resumed, ProcessingEvents.RESUMED, sender=self.processing_service)
        dispatcher.disconnect(self._handle_processing_cancelled, ProcessingEvents.CANCELLED, sender=self.processing_service)

        # Unsubscribe from global events
        dispatcher.disconnect(self._handle_global_processing_changed, ProcessingEvents.STARTED, sender=dispatcher.Any)
        dispatcher.disconnect(self._handle_global_processing_changed, ProcessingEvents.COMPLETED, sender=dispatcher.Any)
        dispatcher.disconnect(self._handle_global_processing_changed, ProcessingEvents.CANCELLED, sender=dispatcher.Any)
        dispatcher.disconnect(self._handle_global_processing_changed, ProcessingEvents.ERROR, sender=dispatcher.Any)
    
    def _validate_current_state(self):
        """Validate current file and column mapping state."""
        if not self.current_file or not self.current_file.valid:
            self.view.set_processing_enabled(False)
            return

        # Check if another platform is processing
        if ProcessingService.is_any_processing():
            self.view.set_processing_enabled(False)
            return

        # Validate column mapping if we have one
        if self.current_column_mapping.post_column:
            validation_result = self.csv_service.validate_column_mapping(
                self.current_file,
                self.current_column_mapping
            )

            if validation_result.valid:
                self.view.set_processing_enabled(True)
                self.view.show_validation_success()
            else:
                self.view.set_processing_enabled(False)
                self.view.show_validation_error(validation_result.error_summary)
        else:
            # No column mapping yet
            self.view.set_processing_enabled(False)
    
    def _validate_processing_request(self) -> bool:
        """Validate that processing can be started."""
        if not self.current_file or not self.current_file.valid:
            self.view.show_processing_error("No valid file loaded")
            return False
        
        if not self.current_column_mapping.is_valid:
            self.view.show_processing_error("Invalid column mapping")
            return False
        
        if self.processing_service.is_processing():
            self.view.show_processing_error("Processing already in progress")
            return False
        
        return True
    
    # Processing service event handlers
    
    def _handle_progress_update(self, sender=None, **kwargs):
        """Handle progress updates from processing service."""
        status = kwargs.get('status')
        if status:
            self.view.update_progress(status)
    
    def _handle_processing_complete(self, sender=None, **kwargs):
        """Handle processing completion."""
        result = kwargs.get('result')
        if result:
            # Log to console (captured by ConsoleLogger)
            print(f"✅ Processing completed: {result.stats}")
            self.view.show_processing_complete(result)
    
    def _handle_processing_error(self, sender=None, **kwargs):
        """Handle processing error."""
        error_message = kwargs.get('error_message', 'Unknown error')
        # Log to console (captured by ConsoleLogger)
        print(f"❌ Processing error: {error_message}")
        self.view.show_processing_error(error_message)
    
    def _handle_processing_started(self, sender=None, **kwargs):
        """Handle processing started."""
        self.view.show_processing_started()
    
    def _handle_processing_paused(self, sender=None, **kwargs):
        """Handle processing paused."""
        self.view.show_processing_paused()
    
    def _handle_processing_resumed(self, sender=None, **kwargs):
        """Handle processing resumed."""
        self.view.show_processing_resumed()
    
    def _handle_processing_cancelled(self, sender=None, **kwargs):
        """Handle processing cancelled."""
        self.view.show_processing_cancelled()

    def _handle_global_processing_changed(self, sender=None, **kwargs):
        """Handle processing state change from any platform - re-validate button state."""
        print(f"🔄 Global processing changed for {self.platform}, is_any_processing={ProcessingService.is_any_processing()}")
        # Re-validate to update button state based on global processing status
        self._validate_current_state()

    # Platform-specific methods (override in subclasses)
    
    def _suggest_columns(self, file_info: FileInfo):
        """
        Suggest appropriate columns for the platform.
        
        Override in platform-specific presenters for custom behavior.
        
        Args:
            file_info: Information about the loaded file
        """
        # Base implementation: suggest first URL-like column
        url_candidates = self.csv_service.get_url_column_candidates(file_info)
        if url_candidates:
            self.view.suggest_url_column(url_candidates[0])
    
    def _get_platform_validation_rules(self) -> Dict[str, Any]:
        """
        Get platform-specific validation rules.
        
        Override in platform-specific presenters for custom validation.
        
        Returns:
            Dictionary of validation rules specific to the platform
        """
        return {}
    
    def get_platform_display_name(self) -> str:
        """
        Get display name for the platform.
        
        Override in platform-specific presenters for custom names.
        
        Returns:
            Human-readable platform name
        """
        return self.platform.title()