"""
Unit tests for CSVService.

Tests CSV file loading, validation, and column mapping operations.
"""

import pytest
import pandas as pd
import os

from services.csv_service import CSVService
from models.file_models import FileInfo, ColumnMapping, ValidationResult


class TestCSVServiceLoadFile:
    """Tests for CSVService.load_file() method."""

    def test_load_valid_csv_file(self, sample_csv_file):
        """Test loading a valid CSV file returns correct FileInfo."""
        service = CSVService()
        file_info = service.load_file(sample_csv_file)

        assert file_info.valid is True
        assert file_info.row_count == 3
        assert len(file_info.columns) == 4
        assert 'VideoUrl' in file_info.columns
        assert 'Title' in file_info.columns
        assert file_info.error_message == ""
        assert file_info.dataframe is not None
        assert len(file_info.dataframe) == 3

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file returns error."""
        service = CSVService()
        file_info = service.load_file('/path/does/not/exist.csv')

        assert file_info.valid is False
        assert "File not found" in file_info.error_message
        assert file_info.row_count == 0
        assert len(file_info.columns) == 0

    def test_load_empty_csv_file(self, empty_csv_file):
        """Test loading an empty CSV file returns error."""
        service = CSVService()
        file_info = service.load_file(empty_csv_file)

        assert file_info.valid is False
        assert "empty" in file_info.error_message.lower()

    def test_load_non_csv_file(self, tmp_path):
        """Test loading a non-CSV file returns error."""
        service = CSVService()
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Not a CSV")

        file_info = service.load_file(str(txt_file))

        assert file_info.valid is False
        assert "must be a CSV file" in file_info.error_message

    def test_load_csv_with_different_delimiter(self, tmp_path):
        """Test loading CSV with tab delimiter."""
        service = CSVService()
        tsv_file = tmp_path / "test.csv"

        # Create tab-separated file
        data = "VideoUrl\tTitle\tChannel\nhttps://youtube.com/1\tVideo1\tChannel1\n"
        tsv_file.write_text(data)

        file_info = service.load_file(str(tsv_file))

        # CSVHandler should auto-detect delimiter
        assert file_info.valid is True
        assert 'VideoUrl' in file_info.columns

    def test_file_info_filename_property(self, sample_csv_file):
        """Test FileInfo.filename property extracts filename correctly."""
        service = CSVService()
        file_info = service.load_file(sample_csv_file)

        assert file_info.filename == os.path.basename(sample_csv_file)
        assert file_info.filename == "test_data.csv"


class TestCSVServiceValidateColumnMapping:
    """Tests for CSVService.validate_column_mapping() method."""

    def test_validate_valid_column_mapping(self, sample_file_info):
        """Test validating a correct column mapping."""
        service = CSVService()
        mapping = ColumnMapping(
            post_column='VideoUrl',
            preserve_columns=['Title', 'Channel']
        )

        result = service.validate_column_mapping(sample_file_info, mapping)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.post_column == 'VideoUrl'
        assert 'Title' in result.preserve_columns
        assert 'Channel' in result.preserve_columns

    def test_validate_mapping_with_invalid_file(self):
        """Test validation fails with invalid file."""
        service = CSVService()
        invalid_file = FileInfo(path="/test.csv", valid=False)
        mapping = ColumnMapping(post_column='VideoUrl')

        result = service.validate_column_mapping(invalid_file, mapping)

        assert result.valid is False
        assert len(result.errors) > 0
        assert "not valid" in result.errors[0].lower()

    def test_validate_mapping_without_post_column(self, sample_file_info):
        """Test validation fails without post column specified."""
        service = CSVService()
        mapping = ColumnMapping(post_column='')

        result = service.validate_column_mapping(sample_file_info, mapping)

        assert result.valid is False
        assert len(result.errors) > 0
        assert "must be selected" in result.errors[0].lower()

    def test_validate_mapping_with_nonexistent_post_column(self, sample_file_info):
        """Test validation fails with non-existent post column."""
        service = CSVService()
        mapping = ColumnMapping(post_column='NonExistentColumn')

        result = service.validate_column_mapping(sample_file_info, mapping)

        assert result.valid is False
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    def test_validate_mapping_with_nonexistent_preserve_column(self, sample_file_info):
        """Test validation fails with non-existent preserve column."""
        service = CSVService()
        mapping = ColumnMapping(
            post_column='VideoUrl',
            preserve_columns=['Title', 'NonExistent']
        )

        result = service.validate_column_mapping(sample_file_info, mapping)

        assert result.valid is False
        assert len(result.errors) > 0
        assert "NonExistent" in result.errors[0]

    def test_validate_mapping_with_empty_preserve_columns(self, sample_file_info):
        """Test validation succeeds with no preserve columns."""
        service = CSVService()
        mapping = ColumnMapping(
            post_column='VideoUrl',
            preserve_columns=[]
        )

        result = service.validate_column_mapping(sample_file_info, mapping)

        assert result.valid is True
        assert len(result.preserve_columns) == 0


class TestCSVServiceGetColumnOptions:
    """Tests for CSVService.get_column_options() method."""

    def test_get_columns_from_valid_file(self, sample_file_info):
        """Test getting column options from valid file."""
        service = CSVService()
        columns = service.get_column_options(sample_file_info)

        assert len(columns) == 4
        assert 'VideoUrl' in columns
        assert 'Title' in columns
        assert 'Channel' in columns
        assert 'Date' in columns

    def test_get_columns_from_invalid_file(self):
        """Test getting columns from invalid file returns empty list."""
        service = CSVService()
        invalid_file = FileInfo(path="/test.csv", valid=False)

        columns = service.get_column_options(invalid_file)

        assert len(columns) == 0


class TestCSVServiceGetUrlColumnCandidates:
    """Tests for CSVService.get_url_column_candidates() method."""

    def test_find_url_column_candidate(self, sample_file_info):
        """Test finding URL column candidate with 'url' keyword."""
        service = CSVService()
        candidates = service.get_url_column_candidates(sample_file_info)

        assert len(candidates) > 0
        assert 'VideoUrl' in candidates

    def test_find_link_column_candidate(self):
        """Test finding column with 'link' keyword."""
        service = CSVService()
        file_info = FileInfo(
            path="/test.csv",
            columns=['video_link', 'title', 'date'],
            valid=True
        )

        candidates = service.get_url_column_candidates(file_info)

        assert len(candidates) == 1
        assert 'video_link' in candidates

    def test_find_multiple_url_candidates(self):
        """Test finding multiple URL column candidates."""
        service = CSVService()
        file_info = FileInfo(
            path="/test.csv",
            columns=['post_url', 'video_link', 'href', 'title'],
            valid=True
        )

        candidates = service.get_url_column_candidates(file_info)

        assert len(candidates) == 3
        assert 'post_url' in candidates
        assert 'video_link' in candidates
        assert 'href' in candidates

    def test_no_url_candidates_found(self):
        """Test when no URL column candidates exist."""
        service = CSVService()
        file_info = FileInfo(
            path="/test.csv",
            columns=['title', 'author', 'date'],
            valid=True
        )

        candidates = service.get_url_column_candidates(file_info)

        assert len(candidates) == 0

    def test_case_insensitive_matching(self):
        """Test URL detection is case-insensitive."""
        service = CSVService()
        file_info = FileInfo(
            path="/test.csv",
            columns=['VIDEO_URL', 'Post_Link', 'HREF'],
            valid=True
        )

        candidates = service.get_url_column_candidates(file_info)

        assert len(candidates) == 3

    def test_url_candidates_from_invalid_file(self):
        """Test getting candidates from invalid file returns empty list."""
        service = CSVService()
        invalid_file = FileInfo(path="/test.csv", valid=False)

        candidates = service.get_url_column_candidates(invalid_file)

        assert len(candidates) == 0


class TestCSVServicePrepareForProcessing:
    """Tests for CSVService.prepare_for_processing() method."""

    def test_prepare_valid_file_for_processing(self, sample_file_info, sample_column_mapping):
        """Test preparing valid file adds result columns."""
        service = CSVService()

        df = service.prepare_for_processing(sample_file_info, sample_column_mapping)

        assert df is not None
        assert len(df) == 3
        # Check that result columns were added
        assert 'status' in df.columns
        assert 'platform' in df.columns
        assert 'timestamp' in df.columns
        assert 'error_message' in df.columns

    def test_prepare_invalid_file_raises_error(self):
        """Test preparing invalid file raises ValueError."""
        service = CSVService()
        invalid_file = FileInfo(path="/test.csv", valid=False)
        mapping = ColumnMapping(post_column='VideoUrl')

        with pytest.raises(ValueError, match="not valid"):
            service.prepare_for_processing(invalid_file, mapping)


class TestCSVServiceGetFileSummary:
    """Tests for CSVService.get_file_summary() method."""

    def test_summary_of_valid_file(self, sample_file_info):
        """Test getting summary of valid file."""
        service = CSVService()
        summary = service.get_file_summary(sample_file_info)

        assert summary['valid'] is True
        assert summary['rows'] == 3
        assert summary['columns'] == 4
        assert len(summary['column_names']) == 4
        assert 'VideoUrl' in summary['column_names']
        assert 'size_mb' in summary

    def test_summary_of_invalid_file(self):
        """Test getting summary of invalid file."""
        service = CSVService()
        invalid_file = FileInfo(
            path="/test.csv",
            valid=False,
            error_message="File not found"
        )

        summary = service.get_file_summary(invalid_file)

        assert summary['valid'] is False
        assert 'error' in summary
        assert summary['error'] == "File not found"
