import pandas as pd
from typing import Dict, List, Tuple
import os


class CSVHandler:
    """Handles CSV file operations, validation, and column mapping."""
    
    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        """Load CSV file with error handling."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                raise ValueError("CSV file is empty")
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