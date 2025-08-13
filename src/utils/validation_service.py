from typing import List, Callable, Optional, Dict, Any
from abc import ABC, abstractmethod
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .validation_manager import ValidationManager, ValidationContext, ValidationResult, ValidationStatus


class ValidationObserver(ABC):
    """Abstract base class for validation observers."""
    
    @abstractmethod
    def on_validation_changed(self, result: ValidationResult, context: ValidationContext):
        """Called when validation state changes."""
        pass


class ValidationEvent:
    """Validation event with context and result."""
    
    def __init__(self, context: ValidationContext, result: ValidationResult):
        self.context = context
        self.result = result
        self.timestamp = None  # Could add timestamp if needed


class ValidationService:
    """Centralized validation service with observer pattern."""
    
    _instance: Optional['ValidationService'] = None
    
    def __new__(cls):
        """Singleton pattern for global validation service."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            self.validation_manager = ValidationManager()
            self.observers: List[ValidationObserver] = []
            self.current_result: Optional[ValidationResult] = None
            self.current_context: Optional[ValidationContext] = None
            self._initialized = True
    
    def subscribe(self, observer: ValidationObserver):
        """Subscribe an observer to validation changes."""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def unsubscribe(self, observer: ValidationObserver):
        """Unsubscribe an observer from validation changes."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate the context and notify observers."""
        # Store current state
        self.current_context = context
        self.current_result = self.validation_manager.validate_all(context)
        
        # Notify all observers
        self._notify_observers(self.current_result, context)
        
        return self.current_result
    
    def get_current_result(self) -> Optional[ValidationResult]:
        """Get the current validation result."""
        return self.current_result
    
    def get_current_context(self) -> Optional[ValidationContext]:
        """Get the current validation context."""
        return self.current_context
    
    def is_valid(self) -> bool:
        """Check if current state is valid."""
        return self.current_result and self.current_result.is_valid()
    
    def _notify_observers(self, result: ValidationResult, context: ValidationContext):
        """Notify all observers of validation change."""
        for observer in self.observers:
            try:
                observer.on_validation_changed(result, context)
            except Exception as e:
                print(f"Error notifying validation observer {observer.__class__.__name__}: {e}")
    
    def clear_validation(self):
        """Clear current validation state."""
        self.current_result = None
        self.current_context = None


# Global validation service instance
validation_service = ValidationService()


class UICommand(ABC):
    """Abstract base class for UI update commands."""
    
    @abstractmethod
    def execute(self, result: ValidationResult, context: ValidationContext):
        """Execute the UI update command."""
        pass


class ButtonStateCommand(UICommand):
    """Command to update button state based on validation."""
    
    def __init__(self, button_id: str, enable_on_valid: bool = True):
        self.button_id = button_id
        self.enable_on_valid = enable_on_valid
    
    def execute(self, result: ValidationResult, context: ValidationContext):
        """Update button enabled/disabled state with visual feedback."""
        try:
            import dearpygui.dearpygui as dpg
            if dpg.does_item_exist(self.button_id):
                enabled = result.is_valid() if self.enable_on_valid else not result.is_valid()
                dpg.configure_item(self.button_id, enabled=enabled)
                
                # Apply visual styling for disabled state
                if not enabled:
                    # Create and apply disabled button theme
                    with dpg.theme() as disabled_button_theme:
                        with dpg.theme_component(dpg.mvButton):
                            dpg.add_theme_color(dpg.mvThemeCol_Text, [80, 80, 80], category=dpg.mvThemeCat_Core)
                            dpg.add_theme_color(dpg.mvThemeCol_Button, [30, 30, 30], category=dpg.mvThemeCat_Core)
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [30, 30, 30], category=dpg.mvThemeCat_Core)
                            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [30, 30, 30], category=dpg.mvThemeCat_Core)
                    dpg.bind_item_theme(self.button_id, disabled_button_theme)
                else:
                    # Remove disabled theme to restore normal appearance
                    dpg.bind_item_theme(self.button_id, 0)  # 0 removes item theme
                    
        except Exception as e:
            print(f"Error updating button {self.button_id}: {e}")


class FileStatusCommand(UICommand):
    """Command to update file status display based on validation."""
    
    def __init__(self, status_container_id: str):
        self.status_container_id = status_container_id
    
    def execute(self, result: ValidationResult, context: ValidationContext):
        """Update file status display."""
        try:
            import dearpygui.dearpygui as dpg
            if not dpg.does_item_exist(self.status_container_id):
                return
            
            # Clear existing content
            dpg.delete_item(self.status_container_id, children_only=True)
            
            if result.is_valid():
                # Show successful validation info
                dpg.add_text(f"{result.csv_filename}", color=[200, 200, 255], parent=self.status_container_id)
                dpg.add_text(f"entries: {result.total_entries}", color=[200, 200, 255], parent=self.status_container_id)
                dpg.add_text(f"Valid post urls: {result.valid_url_count}", color=[200, 200, 255], parent=self.status_container_id)
                
                # Show warnings if any
                for warning in result.warnings:
                    dpg.add_text(f"⚠ {warning}", color=[255, 255, 100], parent=self.status_container_id)
            else:
                # Show validation errors
                for error in result.errors:
                    dpg.add_text(f"❌ {error}", color=[255, 100, 100], parent=self.status_container_id)
                    
        except Exception as e:
            print(f"Error updating file status: {e}")


class ValidationUIController(ValidationObserver):
    """Controller that manages multiple UI commands for validation updates."""
    
    def __init__(self):
        self.commands: List[UICommand] = []
    
    def add_command(self, command: UICommand):
        """Add a UI update command."""
        self.commands.append(command)
    
    def remove_command(self, command: UICommand):
        """Remove a UI update command."""
        if command in self.commands:
            self.commands.remove(command)
    
    def on_validation_changed(self, result: ValidationResult, context: ValidationContext):
        """Execute all UI update commands when validation changes."""
        for command in self.commands:
            command.execute(result, context)