"""Processing job validation."""

from models.processing_models import ProcessingJob, ProcessingState
from models.file_models import ValidationResult


def validate_job(job: ProcessingJob, current_state: ProcessingState) -> ValidationResult:
    """
    Validate that a processing job can be started.

    Args:
        job: Processing job configuration
        current_state: Current processing state

    Returns:
        ValidationResult with errors if any
    """
    result = ValidationResult()

    if current_state != ProcessingState.IDLE:
        result.add_error("Processing is already in progress")
        return result

    if not job.is_valid:
        result.add_error("Invalid job configuration")

    if not job.file_info.valid:
        result.add_error("File is not valid")

    if not job.column_mapping.is_valid:
        result.add_error("Column mapping is not valid")

    if not job.platform:
        result.add_error("Platform must be specified")

    if job.file_info.rows is not None:
        post_column = job.column_mapping.post_column
        if post_column in job.file_info.columns:
            non_empty_count = sum(1 for r in job.file_info.rows if r.get(post_column))
            if non_empty_count == 0:
                result.add_error(f"Post column '{post_column}' contains no valid URLs")

    if not result.errors:
        result.valid = True

    return result
