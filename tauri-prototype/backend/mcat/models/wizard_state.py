"""
State models for wizard and dialog views.

These models hold all UI state that was previously stored in views,
following the MVP pattern where views are completely passive.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict

from models.import_result import UrlImportResult
from models.project_models import RunConfig


@dataclass
class NewProjectWizardState:
    """
    State model for the new project wizard.

    Holds all wizard state including user inputs, CSV data,
    and current step in the wizard flow.
    """

    # Current step (1 = basics, 2 = column mapping)
    current_step: int = 1

    # Step 1 inputs
    name: str = ""
    platform: str = "youtube"
    selected_location: Optional[Path] = None
    selected_csv: Optional[Path] = None

    # CSV data (loaded after CSV selection)
    csv_columns: List[str] = field(default_factory=list)

    # Step 2 inputs
    url_column: str = ""
    preserve_columns: List[str] = field(default_factory=list)

    # Validation
    error_message: str = ""
    has_error: bool = False

    def reset(self) -> None:
        """Reset wizard state to initial values."""
        self.current_step = 1
        self.name = ""
        self.platform = "youtube"
        self.selected_location = None
        self.selected_csv = None
        self.csv_columns = []
        self.url_column = ""
        self.preserve_columns = []
        self.error_message = ""
        self.has_error = False

    def can_proceed_to_step2(self) -> bool:
        """Check if step 1 is complete and can proceed."""
        return bool(
            self.name and
            self.platform and
            self.selected_location and
            self.selected_csv and
            self.selected_csv.exists()
        )

    def can_create_project(self) -> bool:
        """Check if all required data is present to create project."""
        return bool(
            self.can_proceed_to_step2() and
            self.url_column
        )


@dataclass
class AddUrlsDialogState:
    """
    State model for the add URLs dialog.

    Holds selected CSV path and import preview result.
    """

    selected_csv: Optional[Path] = None
    import_result: Optional[UrlImportResult] = None
    error_message: str = ""
    has_error: bool = False

    def reset(self) -> None:
        """Reset dialog state to initial values."""
        self.selected_csv = None
        self.import_result = None
        self.error_message = ""
        self.has_error = False

    def can_import(self) -> bool:
        """Check if import can proceed."""
        return bool(
            self.import_result and
            self.import_result.is_valid and
            not self.has_error
        )


@dataclass
class InterruptedRunDialogState:
    """
    State model for the interrupted run dialog.

    Holds information about the interrupted run to display.
    """

    run: Optional[RunConfig] = None
    processed_count: int = 0
    total_count: int = 0

    def reset(self) -> None:
        """Reset dialog state."""
        self.run = None
        self.processed_count = 0
        self.total_count = 0

    @property
    def remaining_count(self) -> int:
        """Get number of remaining URLs to process."""
        return self.total_count - self.processed_count

    @property
    def details_text(self) -> str:
        """Get formatted details text for display."""
        if not self.run:
            return ""
        return (
            f"Run ID: {self.run.id}\n"
            f"Progress: {self.processed_count}/{self.total_count} URLs processed\n"
            f"Remaining: {self.remaining_count} URLs\n\n"
            f"Would you like to resume this run or start a new one?\n"
            f"(Starting new will mark the interrupted run as abandoned)"
        )
