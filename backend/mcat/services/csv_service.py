"""
CSV file operations service.

Pure business logic for CSV file handling without UI dependencies.
"""

import polars as pl
from typing import List, Dict
import os

from models.file_models import FileInfo, ValidationResult, ColumnMapping
from utils.csv_handler import CSVHandler


class CSVService:
    """Service for CSV file operations and validation."""

    def load_file(self, file_path: str) -> FileInfo:
        """
        Load and parse a CSV file, return structured file information.

        Args:
            file_path: Path to the CSV file

        Returns:
            FileInfo: Structured information about the loaded file
        """
        file_info = FileInfo(path=file_path)

        try:
            # Validate file exists and is readable
            if not os.path.exists(file_path):
                file_info.error_message = f"File not found: {file_path}"
                return file_info

            if not file_path.lower().endswith('.csv'):
                file_info.error_message = "File must be a CSV file"
                return file_info

            # Load the CSV file using existing CSV handler
            dataframe = CSVHandler.load_csv(file_path)

            # Extract file information
            file_info.dataframe = dataframe
            file_info.columns = dataframe.columns
            file_info.row_count = len(dataframe)
            file_info.valid = True

            # Additional validation
            if file_info.row_count == 0:
                file_info.error_message = "CSV file is empty"
                file_info.valid = False
            elif len(file_info.columns) == 0:
                file_info.error_message = "CSV file has no columns"
                file_info.valid = False

        except Exception as e:
            file_info.error_message = f"Error loading CSV file: {str(e)}"
            file_info.valid = False

        return file_info

    def validate_column_mapping(self, file_info: FileInfo, column_mapping: ColumnMapping) -> ValidationResult:
        """
        Validate that the column mapping is valid for the given file.

        Args:
            file_info: Information about the loaded file
            column_mapping: Column mapping configuration

        Returns:
            ValidationResult: Validation result with errors if any
        """
        result = ValidationResult()

        # Check if file is valid first
        if not file_info.valid:
            result.add_error("File is not valid")
            return result

        # Check if post column is specified
        if not column_mapping.post_column:
            result.add_error("Post URL column must be selected")
            return result

        # Check if post column exists in file
        if column_mapping.post_column not in file_info.columns:
            result.add_error(f"Post column '{column_mapping.post_column}' not found in CSV")
            return result

        # If no errors, mark as valid
        if not result.errors:
            result.valid = True
            result.post_column = column_mapping.post_column

        return result

    def get_column_options(self, file_info: FileInfo) -> List[str]:
        """
        Get list of available columns for mapping.

        Args:
            file_info: Information about the loaded file

        Returns:
            List of column names available for selection
        """
        if not file_info.valid:
            return []

        return list(file_info.columns)

    def get_url_column_candidates(self, file_info: FileInfo) -> List[str]:
        """
        Get columns that are likely to contain URLs based on name patterns.

        Args:
            file_info: Information about the loaded file

        Returns:
            List of columns likely to contain URLs
        """
        if not file_info.valid:
            return []

        url_keywords = ['url', 'link', 'post', 'video', 'href', 'address']
        candidates = []

        for column in file_info.columns:
            column_lower = column.lower()
            if any(keyword in column_lower for keyword in url_keywords):
                candidates.append(column)

        return candidates

    def prepare_for_processing(self, file_info: FileInfo, column_mapping: ColumnMapping) -> pl.DataFrame:
        """
        Prepare the CSV data for processing by adding result columns.

        Args:
            file_info: Information about the loaded file
            column_mapping: Column mapping configuration

        Returns:
            DataFrame ready for processing
        """
        if not file_info.valid or file_info.dataframe is None:
            raise ValueError("File is not valid or not loaded")

        # Clone the dataframe
        df = file_info.dataframe.clone()

        # Add result columns using existing CSV handler
        df = CSVHandler.add_result_columns(df)

        return df

    def get_file_summary(self, file_info: FileInfo) -> Dict[str, any]:
        """
        Get a summary of the file for display purposes.

        Args:
            file_info: Information about the loaded file

        Returns:
            Dictionary with file summary information
        """
        if not file_info.valid:
            return {
                'filename': file_info.filename,
                'valid': False,
                'error': file_info.error_message
            }

        return {
            'filename': file_info.filename,
            'valid': True,
            'rows': file_info.row_count,
            'columns': len(file_info.columns),
            'column_names': file_info.columns,
            'size_mb': round(file_info.dataframe.estimated_size() / (1024 * 1024), 2) if file_info.dataframe is not None else 0
        }
