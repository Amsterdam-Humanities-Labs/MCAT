"""
Event system for MCAT application using PyDispatcher.

This module provides a centralized event system for loose coupling between
services and presenters, while maintaining direct calls for presenter-view
communication.
"""

from pydispatch import dispatcher
from .event_types import ProcessingEvents, FileEvents

# Re-export dispatcher for convenience
__all__ = [
    'dispatcher',
    'ProcessingEvents',
    'FileEvents'
]
