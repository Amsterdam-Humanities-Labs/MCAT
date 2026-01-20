import pandas as pd
from typing import Dict, List, Tuple, Any
import os
import csv
import threading


class CSVHandler:
    """Handles CSV file operations, validation, and column mapping."""
    
    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        """Load CSV file with automatic delimiter detection."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            # Use pandas' automatic delimiter detection
            df = pd.read_csv(file_path, sep=None, engine='python')
            if df.empty:
                raise ValueError("CSV file is empty")
            print("Successfully loaded CSV with automatic delimiter detection")
            return df
        except Exception as e:
            raise Exception(f"Error loading CSV file: {e}")
    
    @staticmethod
    def validate_column_mapping(df: pd.DataFrame, column_mapping: Dict[str, str]) -> Tuple[bool, str]:
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
    def get_urls_from_column(df: pd.DataFrame, url_column: str) -> List[str]:
        """Extract URLs from the specified column."""
        if url_column not in df.columns:
            raise ValueError(f"URL column '{url_column}' not found in CSV")
        
        urls = df[url_column].dropna().astype(str).tolist()
        if not urls:
            raise ValueError(f"No URLs found in column '{url_column}'")
        
        return urls
    
    @staticmethod
    def add_result_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Add result columns to the DataFrame if they don't exist."""
        result_columns = ['status', 'platform', 'info', 'timestamp', 'error_message']
        
        for col in result_columns:
            if col not in df.columns:
                df[col] = ''
        
        return df
    
    @staticmethod
    def update_results(df: pd.DataFrame, results: List[Dict], url_column: str) -> pd.DataFrame:
        """Update DataFrame with scraping results."""
        # Create a mapping of URL to result
        url_to_result = {result['url']: result for result in results}
        
        # Update each row based on URL match
        for index, row in df.iterrows():
            url = str(row[url_column])
            if url in url_to_result:
                result = url_to_result[url]
                for key, value in result.items():
                    if key in df.columns:
                        df.at[index, key] = value
        
        return df
    
    @staticmethod
    def save_csv(df: pd.DataFrame, output_path: str) -> bool:
        """Save DataFrame to CSV file."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            df.to_csv(output_path, index=False)
            return True
        except Exception as e:
            raise Exception(f"Error saving CSV file: {e}")
    
    @staticmethod
    def get_csv_info(df: pd.DataFrame) -> Dict:
        """Get basic information about the CSV file."""
        return {
            'rows': len(df),
            'columns': list(df.columns),
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
                print(f"⚠️ Failed to write row to CSV: {e}")