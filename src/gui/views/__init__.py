"""
Views for MCAT application.

This module contains the view classes for the project-based UI.
"""

from .start_screen import StartScreen
from .new_project_wizard import NewProjectWizard
from .project_view import ProjectView
from .add_urls_dialog import AddUrlsDialog
from .interrupted_run_dialog import InterruptedRunDialog

__all__ = [
    'StartScreen',
    'NewProjectWizard',
    'ProjectView',
    'AddUrlsDialog',
    'InterruptedRunDialog',
]
