"""
Data models for file operations and validation.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd


@dataclass
class FileInfo:
    """Information about a loaded CSV file."""
    
    path: str
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    valid: bool = False
    error_message: str = ""
    dataframe: Optional[pd.DataFrame] = None
    
    @property
    def filename(self) -> str:
        """Get just the filename from the path."""
        import os
        return os.path.basename(self.path)
    
    @property
    def is_empty(self) -> bool:
        """Check if the file has no rows."""
        return self.row_count == 0


@dataclass
class ValidationResult:
    """Result of validating file and column mappings."""
    
    valid: bool = False
    errors: List[str] = field(default_factory=list)
    post_column: str = ""
    preserve_columns: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error to the validation result."""
        self.errors.append(error)
        self.valid = False
    
    def clear_errors(self) -> None:
        """Clear all errors and mark as valid."""
        self.errors.clear()
        self.valid = True
    
    @property
    def error_summary(self) -> str:
        """Get a summary of all errors."""
        if not self.errors:
            return ""
        return "; ".join(self.errors)


@dataclass
class ColumnMapping:
    """Column mapping configuration."""
    
    post_column: str = ""
    preserve_columns: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if the mapping has required fields."""
        return bool(self.post_column)
    
    @property
    def all_columns(self) -> List[str]:
        """Get all columns that will be used."""
        columns = []
        if self.post_column:
            columns.append(self.post_column)
        columns.extend(self.preserve_columns)
        return columns