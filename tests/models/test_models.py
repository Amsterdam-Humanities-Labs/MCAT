"""
Unit tests for data models.

Tests dataclass properties, validation, and business logic.
"""

import pytest
import pandas as pd

from models.file_models import FileInfo, ColumnMapping, ValidationResult
from models.processing_models import ProcessingJob, ProcessingStatus, ProcessingState, ProcessingResult


class TestFileInfo:
    """Tests for FileInfo dataclass."""

    def test_filename_property(self):
        """Test filename property extracts basename from path."""
        file_info = FileInfo(path="/home/user/documents/data.csv")

        assert file_info.filename == "data.csv"

    def test_is_empty_property_with_zero_rows(self):
        """Test is_empty returns True for zero rows."""
        file_info = FileInfo(path="/test.csv", row_count=0)

        assert file_info.is_empty is True

    def test_is_empty_property_with_rows(self):
        """Test is_empty returns False when rows exist."""
        file_info = FileInfo(path="/test.csv", row_count=10)

        assert file_info.is_empty is False

    def test_default_values(self):
        """Test FileInfo initializes with correct defaults."""
        file_info = FileInfo(path="/test.csv")

        assert file_info.columns == []
        assert file_info.row_count == 0
        assert file_info.valid is False
        assert file_info.error_message == ""
        assert file_info.dataframe is None


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_add_error_marks_invalid(self):
        """Test add_error() sets valid to False."""
        result = ValidationResult()
        result.valid = True

        result.add_error("Test error")

        assert result.valid is False
        assert len(result.errors) == 1
        assert "Test error" in result.errors

    def test_add_multiple_errors(self):
        """Test adding multiple errors accumulates them."""
        result = ValidationResult()

        result.add_error("Error 1")
        result.add_error("Error 2")
        result.add_error("Error 3")

        assert len(result.errors) == 3
        assert result.valid is False

    def test_clear_errors_marks_valid(self):
        """Test clear_errors() removes all errors and marks valid."""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_error("Error 2")

        result.clear_errors()

        assert len(result.errors) == 0
        assert result.valid is True

    def test_error_summary_with_no_errors(self):
        """Test error_summary returns empty string when no errors."""
        result = ValidationResult()

        assert result.error_summary == ""

    def test_error_summary_with_single_error(self):
        """Test error_summary with one error."""
        result = ValidationResult()
        result.add_error("Test error")

        assert result.error_summary == "Test error"

    def test_error_summary_with_multiple_errors(self):
        """Test error_summary joins multiple errors."""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_error("Error 2")

        summary = result.error_summary
        assert "Error 1" in summary
        assert "Error 2" in summary
        assert ";" in summary


class TestColumnMapping:
    """Tests for ColumnMapping dataclass."""

    def test_is_valid_with_post_column(self):
        """Test is_valid returns True when post_column is set."""
        mapping = ColumnMapping(post_column='VideoUrl')

        assert mapping.is_valid is True

    def test_is_valid_without_post_column(self):
        """Test is_valid returns False when post_column is empty."""
        mapping = ColumnMapping(post_column='')

        assert mapping.is_valid is False

    def test_all_columns_property(self):
        """Test all_columns returns post_column + preserve_columns."""
        mapping = ColumnMapping(
            post_column='VideoUrl',
            preserve_columns=['Title', 'Channel', 'Date']
        )

        all_cols = mapping.all_columns

        assert len(all_cols) == 4
        assert 'VideoUrl' in all_cols
        assert 'Title' in all_cols
        assert 'Channel' in all_cols
        assert 'Date' in all_cols

    def test_all_columns_with_no_preserve(self):
        """Test all_columns with only post_column."""
        mapping = ColumnMapping(post_column='VideoUrl')

        all_cols = mapping.all_columns

        assert len(all_cols) == 1
        assert 'VideoUrl' in all_cols


class TestProcessingState:
    """Tests for ProcessingState enum."""

    def test_all_states_defined(self):
        """Test all expected processing states exist."""
        assert ProcessingState.IDLE.value == "idle"
        assert ProcessingState.VALIDATING.value == "validating"
        assert ProcessingState.PROCESSING.value == "processing"
        assert ProcessingState.PAUSED.value == "paused"
        assert ProcessingState.COMPLETED.value == "completed"
        assert ProcessingState.ERROR.value == "error"
        assert ProcessingState.CANCELLED.value == "cancelled"


class TestProcessingJob:
    """Tests for ProcessingJob dataclass."""

    def test_is_valid_with_complete_job(self, sample_file_info, sample_column_mapping):
        """Test is_valid returns True for complete job configuration."""
        job = ProcessingJob(
            file_info=sample_file_info,
            column_mapping=sample_column_mapping,
            platform='youtube'
        )

        assert job.is_valid is True

    def test_is_valid_with_invalid_file(self, sample_column_mapping):
        """Test is_valid returns False with invalid file."""
        invalid_file = FileInfo(path="/test.csv", valid=False)
        job = ProcessingJob(
            file_info=invalid_file,
            column_mapping=sample_column_mapping,
            platform='youtube'
        )

        assert job.is_valid is False

    def test_is_valid_with_invalid_mapping(self, sample_file_info):
        """Test is_valid returns False with invalid column mapping."""
        invalid_mapping = ColumnMapping(post_column='')
        job = ProcessingJob(
            file_info=sample_file_info,
            column_mapping=invalid_mapping,
            platform='youtube'
        )

        assert job.is_valid is False

    def test_is_valid_without_platform(self, sample_file_info, sample_column_mapping):
        """Test is_valid returns False without platform."""
        job = ProcessingJob(
            file_info=sample_file_info,
            column_mapping=sample_column_mapping,
            platform=''
        )

        assert job.is_valid is False

    def test_default_platform(self, sample_file_info, sample_column_mapping):
        """Test default platform is youtube."""
        job = ProcessingJob(
            file_info=sample_file_info,
            column_mapping=sample_column_mapping
        )

        assert job.platform == 'youtube'


class TestProcessingStatus:
    """Tests for ProcessingStatus dataclass."""

    def test_progress_percentage_calculation(self):
        """Test progress_percentage calculates correctly."""
        status = ProcessingStatus(total_count=100, processed_count=25)

        assert status.progress_percentage == 25.0

    def test_progress_percentage_with_zero_total(self):
        """Test progress_percentage returns 0 when total is 0."""
        status = ProcessingStatus(total_count=0, processed_count=0)

        assert status.progress_percentage == 0.0

    def test_progress_percentage_at_completion(self):
        """Test progress_percentage is 100 at completion."""
        status = ProcessingStatus(total_count=50, processed_count=50)

        assert status.progress_percentage == 100.0

    def test_is_complete_with_completed_state(self):
        """Test is_complete returns True for COMPLETED state."""
        status = ProcessingStatus(state=ProcessingState.COMPLETED)

        assert status.is_complete is True

    def test_is_complete_with_error_state(self):
        """Test is_complete returns True for ERROR state."""
        status = ProcessingStatus(state=ProcessingState.ERROR)

        assert status.is_complete is True

    def test_is_complete_with_cancelled_state(self):
        """Test is_complete returns True for CANCELLED state."""
        status = ProcessingStatus(state=ProcessingState.CANCELLED)

        assert status.is_complete is True

    def test_is_complete_with_processing_state(self):
        """Test is_complete returns False for PROCESSING state."""
        status = ProcessingStatus(state=ProcessingState.PROCESSING)

        assert status.is_complete is False

    def test_is_running_with_processing_state(self):
        """Test is_running returns True for PROCESSING state."""
        status = ProcessingStatus(state=ProcessingState.PROCESSING)

        assert status.is_running is True

    def test_is_running_with_other_states(self):
        """Test is_running returns False for non-PROCESSING states."""
        status = ProcessingStatus(state=ProcessingState.PAUSED)
        assert status.is_running is False

        status.state = ProcessingState.COMPLETED
        assert status.is_running is False

    def test_is_paused_with_paused_state(self):
        """Test is_paused returns True for PAUSED state."""
        status = ProcessingStatus(state=ProcessingState.PAUSED)

        assert status.is_paused is True

    def test_is_paused_with_other_states(self):
        """Test is_paused returns False for non-PAUSED states."""
        status = ProcessingStatus(state=ProcessingState.PROCESSING)

        assert status.is_paused is False

    def test_default_stats_initialization(self):
        """Test stats dictionary initializes with correct defaults."""
        status = ProcessingStatus()

        assert status.stats['live'] == 0
        assert status.stats['removed'] == 0
        assert status.stats['restricted'] == 0
        assert status.stats['errors'] == 0


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""

    def test_default_values(self):
        """Test ProcessingResult initializes with correct defaults."""
        result = ProcessingResult()

        assert result.success is False
        assert result.dataframe is None
        assert result.stats == {}
        assert result.processed_count == 0
        assert result.error_message == ""

    def test_successful_result(self):
        """Test creating a successful result."""
        df = pd.DataFrame({'VideoUrl': ['url1', 'url2']})
        result = ProcessingResult(
            success=True,
            dataframe=df,
            stats={'live': 2},
            processed_count=2
        )

        assert result.success is True
        assert result.dataframe is not None
        assert len(result.dataframe) == 2
        assert result.processed_count == 2

    def test_error_result(self):
        """Test creating an error result."""
        result = ProcessingResult(
            success=False,
            error_message="Processing failed"
        )

        assert result.success is False
        assert result.error_message == "Processing failed"
        assert result.dataframe is None
