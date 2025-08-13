import pandas as pd
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ValidationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"


class ValidationResult:
    def __init__(self):
        self.status: ValidationStatus = ValidationStatus.PENDING
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.valid_url_count: int = 0
        self.total_entries: int = 0
        self.csv_filename: str = ""
    
    def is_valid(self) -> bool:
        return self.status == ValidationStatus.VALID and len(self.errors) == 0
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.status = ValidationStatus.INVALID
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)


class ValidationContext:
    def __init__(self):
        self.csv_df: Optional[pd.DataFrame] = None
        self.csv_filename: str = ""
        self.column_mapping: Dict[str, str] = {}
        self.csv_columns: List[str] = []


class ValidationManager:
    """Manages real-time validation of CSV data and column mappings."""
    
    def __init__(self):
        self.url_pattern = re.compile(
            r'https?://'  # http:// or https://
            r'(?:[-\w.])+' # domain
            r'(?:\.[a-zA-Z]{2,})?' # TLD
            r'(?::[0-9]+)?' # optional port
            r'(?:/[^\s]*)?', # path
            re.IGNORECASE
        )
    
    def validate_all(self, context: ValidationContext) -> ValidationResult:
        """Run all validation checks on the current context."""
        result = ValidationResult()
        
        # Set basic info
        result.csv_filename = context.csv_filename
        if context.csv_df is not None:
            result.total_entries = len(context.csv_df)
        
        # 1. CSV Structure Validation
        if not self._validate_csv_structure(context, result):
            return result
        
        # 2. Column Mapping Validation
        if not self._validate_column_mapping(context, result):
            return result
        
        # 3. Data Content Validation (URL structure only)
        if not self._validate_data_content(context, result):
            return result
        
        # If we get here, validation passed
        result.status = ValidationStatus.VALID
        return result
    
    def _validate_csv_structure(self, context: ValidationContext, result: ValidationResult) -> bool:
        """Validate basic CSV structure."""
        if context.csv_df is None:
            result.add_error("No CSV file loaded")
            return False
        
        if len(context.csv_df) == 0:
            result.add_error("CSV file is empty")
            return False
        
        if len(context.csv_df.columns) == 0:
            result.add_error("CSV file has no columns")
            return False
        
        return True
    
    def _validate_column_mapping(self, context: ValidationContext, result: ValidationResult) -> bool:
        """Validate column mappings."""
        # Check that post column is mapped (required)
        post_column = context.column_mapping.get('post', '')
        if not post_column or post_column == '[none]':
            result.add_error("Post column must be selected")
            return False
        
        # Check that mapped columns exist in CSV
        for col_type, mapped_col in context.column_mapping.items():
            if mapped_col and mapped_col != '[none]' and mapped_col not in context.csv_columns:
                result.add_error(f"Selected {col_type} column '{mapped_col}' not found in CSV")
                return False
        
        return True
    
    def _validate_data_content(self, context: ValidationContext, result: ValidationResult) -> bool:
        """Validate data content, specifically URL structure."""
        post_column = context.column_mapping.get('post', '')
        if not post_column or post_column == '[none]':
            return False
        
        # Check URLs in post column
        if post_column in context.csv_df.columns:
            post_data = context.csv_df[post_column].dropna()
            valid_url_count = 0
            
            for url in post_data:
                if self._is_valid_url_structure(str(url)):
                    valid_url_count += 1
            
            result.valid_url_count = valid_url_count
            
            if valid_url_count == 0:
                result.add_error("No valid URLs found in post column")
                return False
            
            # Add warning if some URLs are invalid
            invalid_count = len(post_data) - valid_url_count
            if invalid_count > 0:
                result.add_warning(f"{invalid_count} invalid URLs will be skipped")
        
        return True
    
    def _is_valid_url_structure(self, url: str) -> bool:
        """Check if URL has valid structure (no platform-specific validation)."""
        if not url or pd.isna(url) or str(url).strip() == '':
            return False
        
        url = str(url).strip()
        return bool(self.url_pattern.match(url))
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """Generate a summary string for display in file status."""
        if not result.is_valid():
            return f"Validation failed: {'; '.join(result.errors)}"
        
        summary_parts = []
        if result.csv_filename:
            summary_parts.append(f"{result.csv_filename}")
        if result.total_entries > 0:
            summary_parts.append(f"entries: {result.total_entries}")
        if result.valid_url_count > 0:
            summary_parts.append(f"Valid post urls: {result.valid_url_count}")
        
        return '\n'.join(summary_parts) if summary_parts else "No data to validate"