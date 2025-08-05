from enum import Enum
from typing import Callable, Dict, List, Any
import threading


class ProcessingState(Enum):
    """Processing states for the application."""
    IDLE = "Ready"
    LOADING_CSV = "Loading CSV file..."
    VALIDATING_DATA = "Validating data format..."
    INITIALIZING_SCRAPERS = "Setting up scrapers..."
    PROCESSING_URLS = "Processing URLs..."
    FINALIZING_RESULTS = "Finalizing results..."
    COMPLETED = "Processing completed"
    ERROR = "Error occurred"
    CANCELLED = "Processing cancelled"


class StateManager:
    """Centralized state management and broadcasting for the application."""
    
    def __init__(self):
        self._current_state = ProcessingState.IDLE
        self._subscribers: List[Callable] = []
        self._progress_data = {
            'current': 0,
            'total': 0,
            'stats': {
                'live': 0,
                'removed': 0,
                'restricted': 0,
                'errors': 0
            },
            'current_action': ''
        }
        self._lock = threading.Lock()
    
    def broadcast_state(self, state: ProcessingState, data: Dict = None):
        """Broadcast state change to all subscribers."""
        with self._lock:
            self._current_state = state
            if data:
                self._progress_data.update(data)
            
            # Notify all subscribers
            for callback in self._subscribers:
                try:
                    callback(state, self._progress_data.copy())
                except Exception as e:
                    print(f"Error in state callback: {e}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to state changes."""
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from state changes."""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
    
    def get_current_state(self) -> ProcessingState:
        """Get the current processing state."""
        with self._lock:
            return self._current_state
    
    def update_progress(self, current: int, total: int, stats: Dict = None, current_action: str = ""):
        """Update progress information."""
        data = {
            'current': current,
            'total': total,
            'current_action': current_action
        }
        if stats:
            data['stats'] = stats
        
        self.broadcast_state(self._current_state, data)
    
    def reset(self):
        """Reset state manager to initial state."""
        with self._lock:
            self._current_state = ProcessingState.IDLE
            self._progress_data = {
                'current': 0,
                'total': 0,
                'stats': {
                    'live': 0,
                    'removed': 0,
                    'restricted': 0,
                    'errors': 0
                },
                'current_action': ''
            }
    
    def get_progress_data(self) -> Dict:
        """Get current progress data."""
        with self._lock:
            return self._progress_data.copy()