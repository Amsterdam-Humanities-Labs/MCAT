# MCAT Test Suite

Unit and integration tests for the MCAT (Content Moderation Analysis Toolkit) application.

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=src --cov-report=html
```

### Run specific test file
```bash
pytest tests/services/test_csv_service.py
```

### Run specific test class
```bash
pytest tests/services/test_csv_service.py::TestCSVServiceLoadFile
```

### Run specific test
```bash
pytest tests/services/test_csv_service.py::TestCSVServiceLoadFile::test_load_valid_csv_file
```

### Run tests by marker
```bash
pytest -m unit          # Run only unit tests (fast)
pytest -m integration   # Run integration tests
pytest -m "not slow"    # Skip slow tests
```

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── models/                  # Data model tests
│   └── test_models.py       # FileInfo, ProcessingStatus, etc.
├── services/                # Service layer tests
│   ├── test_csv_service.py  # CSV operations
│   └── test_processing_service.py (TODO)
├── scrapers/                # Scraper tests
│   └── test_youtube_scraper.py
├── presenters/              # Presenter tests (TODO)
├── events/                  # Event system tests (TODO)
└── utils/                   # Utility tests (TODO)
```

## Test Markers

- `@pytest.mark.unit` - Fast, isolated unit tests (default)
- `@pytest.mark.integration` - Tests involving multiple components
- `@pytest.mark.slow` - Slow tests (network, Selenium)

## Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_csv_data` - Pandas DataFrame with test data
- `sample_csv_file` - Temporary CSV file
- `empty_csv_file` - Empty CSV file
- `sample_file_info` - Valid FileInfo object
- `sample_column_mapping` - Valid ColumnMapping
- `sample_processing_job` - Valid ProcessingJob
- `mock_view` - Mock view for presenter tests

## Coverage Goals

- **Services**: 90%+ coverage (critical business logic)
- **Models**: 90%+ coverage (data validation)
- **Scrapers**: 80%+ coverage (core detection logic)
- **Presenters**: 70%+ coverage (coordination logic)
- **GUI**: No coverage required (manual testing)

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Test Structure (AAA Pattern)
```python
def test_something(self):
    # Arrange - Set up test data
    service = CSVService()
    file_path = "/path/to/test.csv"

    # Act - Execute the code under test
    result = service.load_file(file_path)

    # Assert - Verify the outcome
    assert result.valid is True
```

## TODO: Tests to Add

High priority:
- [ ] `test_processing_service.py` - Threading, pause/resume
- [ ] `test_base_tab_presenter.py` - Presenter workflow
- [ ] `test_event_system.py` - Event bus behavior
- [ ] `test_csv_handler.py` - Low-level CSV operations

Medium priority:
- [ ] `test_validation_service.py` - Validation observer pattern
- [ ] Integration tests for full workflow
- [ ] Performance tests for large CSV files

Low priority:
- [ ] `test_batch_processor.py` - Batch processing
- [ ] `test_driver_manager.py` - WebDriver pool
