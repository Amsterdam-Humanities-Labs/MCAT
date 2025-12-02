"""
Data models for MCAT application.

This module contains data classes and models used throughout the application
for representing files, validation results, and processing jobs.
"""

from .file_models import FileInfo, ValidationResult
from .processing_models import ProcessingJob, ProcessingStatus

__all__ = [
    'FileInfo',
    'ValidationResult', 
    'ProcessingJob',
    'ProcessingStatus'
]