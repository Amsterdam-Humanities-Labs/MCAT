"""Event system for MCAT application using PyDispatcher."""

from pydispatch import dispatcher
from .event_types import ProcessingEvents

__all__ = [
    'dispatcher',
    'ProcessingEvents',
]
