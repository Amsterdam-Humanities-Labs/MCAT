"""
Pytest configuration and shared fixtures for MCAT tests.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path

from models.file_models import FileInfo, ColumnMapping, ValidationResult
from models.processing_models import ProcessingJob, ProcessingStatus, ProcessingState


@pytest.fixture
def sample_csv_data():
    """Sample CSV data as a pandas DataFrame."""
    return pd.DataFrame({
        'VideoUrl': [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/watch?v=jNQXAC9IVRw',
            'https://www.youtube.com/watch?v=9bZkp7q19f0'
        ],
        'Title': ['Video 1', 'Video 2', 'Video 3'],
        'Channel': ['Channel A', 'Channel B', 'Channel C'],
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03']
    })


@pytest.fixture
def sample_csv_file(sample_csv_data, tmp_path):
    """Create a temporary CSV file with sample data."""
    csv_file = tmp_path / "test_data.csv"
    sample_csv_data.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def empty_csv_file(tmp_path):
    """Create a CSV file with headers but no data rows."""
    csv_file = tmp_path / "empty.csv"
    # Create CSV with headers but no rows
    df = pd.DataFrame(columns=['VideoUrl', 'Title', 'Channel'])
    df.to_csv(csv_file, index=False)
    return str(csv_file)


@pytest.fixture
def invalid_csv_file(tmp_path):
    """Create a file that's not a valid CSV."""
    file_path = tmp_path / "invalid.txt"
    file_path.write_text("This is not a CSV file")
    return str(file_path)


@pytest.fixture
def sample_file_info(sample_csv_data):
    """Sample FileInfo object with valid data."""
    return FileInfo(
        path="/path/to/test.csv",
        columns=['VideoUrl', 'Title', 'Channel', 'Date'],
        row_count=3,
        valid=True,
        dataframe=sample_csv_data
    )


@pytest.fixture
def sample_column_mapping():
    """Sample ColumnMapping configuration."""
    return ColumnMapping(
        post_column='VideoUrl',
        preserve_columns=['Title', 'Channel', 'Date']
    )


@pytest.fixture
def sample_processing_job(sample_file_info, sample_column_mapping):
    """Sample ProcessingJob configuration."""
    return ProcessingJob(
        file_info=sample_file_info,
        column_mapping=sample_column_mapping,
        platform='youtube'
    )


@pytest.fixture
def sample_processing_status():
    """Sample ProcessingStatus object."""
    return ProcessingStatus(
        state=ProcessingState.PROCESSING,
        total_count=100,
        processed_count=50,
        current_action="Processing video 50/100",
        stats={
            'live': 30,
            'removed': 10,
            'restricted': 5,
            'errors': 5
        }
    )


@pytest.fixture
def mock_view():
    """Mock view object for presenter tests."""
    class MockView:
        def __init__(self):
            self.calls = []

        def show_file_success(self, file_info):
            self.calls.append(('show_file_success', file_info))

        def show_file_error(self, error_message):
            self.calls.append(('show_file_error', error_message))

        def populate_columns(self, columns):
            self.calls.append(('populate_columns', columns))

        def show_processing_started(self):
            self.calls.append(('show_processing_started',))

        def update_progress(self, status):
            self.calls.append(('update_progress', status))

        def show_processing_complete(self, result):
            self.calls.append(('show_processing_complete', result))

        def show_processing_error(self, error_message):
            self.calls.append(('show_processing_error', error_message))

        def show_processing_paused(self):
            self.calls.append(('show_processing_paused',))

        def show_processing_resumed(self):
            self.calls.append(('show_processing_resumed',))

        def show_processing_cancelled(self):
            self.calls.append(('show_processing_cancelled',))

        def get_call_count(self, method_name):
            return sum(1 for call in self.calls if call[0] == method_name)

        def get_last_call(self, method_name):
            for call in reversed(self.calls):
                if call[0] == method_name:
                    return call
            return None

    return MockView()
