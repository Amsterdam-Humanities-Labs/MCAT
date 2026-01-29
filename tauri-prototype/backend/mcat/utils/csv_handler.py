import polars as pl
from typing import Dict, List, Tuple, Any
import os
import csv
import threading


class CSVHandler:
    """Handles CSV file operations, validation, and column mapping."""

    @staticmethod
    def load_csv(file_path: str) -> pl.DataFrame:
        """Load CSV file with automatic delimiter detection."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            # Try common delimiters
            for separator in [',', ';', '\t', '|']:
                try:
                    df = pl.read_csv(file_path, separator=separator)
                    if len(df.columns) > 1 or separator == ',':
                        if len(df) == 0:
                            raise ValueError("CSV file is empty")
                        print(f"Successfully loaded CSV with delimiter '{separator}'")
                        return df
                except Exception:
                    continue

            # Default to comma
            df = pl.read_csv(file_path)
            if len(df) == 0:
                raise ValueError("CSV file is empty")
            print("Successfully loaded CSV with default delimiter")
            return df
        except Exception as e:
            raise Exception(f"Error loading CSV file: {e}")

    @staticmethod
    def validate_column_mapping(df: pl.DataFrame, column_mapping: Dict[str, str]) -> Tuple[bool, str]:
        """Validate that mapped columns exist in the DataFrame."""
        missing_columns = []

        for col_type, col_name in column_mapping.items():
            if col_name and col_name not in df.columns:
                missing_columns.append(f"{col_type} column '{col_name}'")

        if missing_columns:
            error_msg = f"Missing columns: {', '.join(missing_columns)}"
            return False, error_msg

        return True, ""

    @staticmethod
    def get_urls_from_column(df: pl.DataFrame, url_column: str) -> List[str]:
        """Extract URLs from the specified column."""
        if url_column not in df.columns:
            raise ValueError(f"URL column '{url_column}' not found in CSV")

        urls = df.select(pl.col(url_column).drop_nulls().cast(pl.Utf8)).to_series().to_list()
        if not urls:
            raise ValueError(f"No URLs found in column '{url_column}'")

        return urls

    @staticmethod
    def add_result_columns(df: pl.DataFrame) -> pl.DataFrame:
        """Add result columns to the DataFrame if they don't exist."""
        result_columns = ['status', 'platform', 'info', 'timestamp', 'error_message']

        for col in result_columns:
            if col not in df.columns:
                df = df.with_columns(pl.lit('').alias(col))

        return df

    @staticmethod
    def update_results(df: pl.DataFrame, results: List[Dict], url_column: str) -> pl.DataFrame:
        """Update DataFrame with scraping results."""
        # Create a mapping of URL to result
        url_to_result = {result['url']: result for result in results}

        # Convert to list of dicts, update, and convert back
        rows = df.to_dicts()
        for row in rows:
            url = str(row.get(url_column, ''))
            if url in url_to_result:
                result = url_to_result[url]
                for key, value in result.items():
                    if key in df.columns:
                        row[key] = value

        return pl.DataFrame(rows)

    @staticmethod
    def save_csv(df: pl.DataFrame, output_path: str) -> bool:
        """Save DataFrame to CSV file."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            df.write_csv(output_path)
            return True
        except Exception as e:
            raise Exception(f"Error saving CSV file: {e}")

    @staticmethod
    def get_csv_info(df: pl.DataFrame) -> Dict:
        """Get basic information about the CSV file."""
        return {
            'rows': len(df),
            'columns': df.columns,
            'column_count': len(df.columns)
        }


class IncrementalCSVWriter:
    """Thread-safe incremental CSV writer for real-time result saving."""

    def __init__(self, output_path: str, columns: List[str]) -> None:
        """
        Initialize incremental CSV writer.

        Args:
            output_path: Path to output CSV file
            columns: List of column names for the CSV
        """
        self.output_path: str = output_path
        self.columns: List[str] = columns
        self.lock: threading.Lock = threading.Lock()
        self.initialized: bool = False

    def write_header(self) -> None:
        """Write CSV header (call once at start)."""
        with self.lock:
            # Ensure output directory exists
            output_dir = os.path.dirname(self.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
            self.initialized = True

    def append_row(self, row_data: Dict[str, Any]) -> None:
        """
        Append a single result row (thread-safe).

        Args:
            row_data: Dictionary of column name to value
        """
        if not self.initialized:
            raise Exception("Must call write_header() first")

        with self.lock:
            try:
                with open(self.output_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.columns)
                    writer.writerow(row_data)
            except Exception as e:
                # Log error but don't crash processing
                print(f"Warning: Failed to write row to CSV: {e}")
