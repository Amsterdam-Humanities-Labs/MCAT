"""
Data models for MCAT application.

This module contains data classes and models used throughout the application
for representing files, validation results, processing jobs, and projects.
"""

from .file_models import FileInfo, ValidationResult, ColumnMapping
from .processing_models import ProcessingJob, ProcessingStatus, ProcessingState
from .project_models import ProjectConfig, RunConfig, RunStatus
from .project_state import ProjectState
from .import_result import UrlImportResult
from .navigation_state import NavigationState, Screen
from .wizard_state import NewProjectWizardState, AddUrlsDialogState, InterruptedRunDialogState

__all__ = [
    # File models
    'FileInfo',
    'ValidationResult',
    'ColumnMapping',
    # Processing models
    'ProcessingJob',
    'ProcessingStatus',
    'ProcessingState',
    # Project models
    'ProjectConfig',
    'RunConfig',
    'RunStatus',
    'ProjectState',
    'UrlImportResult',
    # Navigation models
    'NavigationState',
    'Screen',
    # Wizard/dialog state models
    'NewProjectWizardState',
    'AddUrlsDialogState',
    'InterruptedRunDialogState',
]
