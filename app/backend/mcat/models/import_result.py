"""
Data models for URL import operations.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UrlImportResult:
    """
    Result of previewing a URL import operation.

    Contains information about what will happen if the import is confirmed,
    including counts of new URLs vs duplicates.
    """

    total_in_file: int = 0
    new_urls: int = 0
    duplicates_skipped: int = 0
    rows_to_add: list[dict[str, Any]] = field(default_factory=list)
    error_message: str = ""

    @property
    def has_new_urls(self) -> bool:
        """Check if there are new URLs to import."""
        return self.new_urls > 0

    @property
    def has_error(self) -> bool:
        """Check if there was an error during preview."""
        return bool(self.error_message)

    @property
    def is_valid(self) -> bool:
        """Check if the import result is valid and has URLs to add."""
        return not self.has_error and self.has_new_urls

    @property
    def summary(self) -> str:
        """Get a human-readable summary of the import preview."""
        if self.has_error:
            return f"Error: {self.error_message}"

        if self.duplicates_skipped > 0:
            return (
                f"Found {self.total_in_file} URLs: "
                f"{self.new_urls} new, {self.duplicates_skipped} duplicates (will be skipped)"
            )
        else:
            return f"Found {self.new_urls} new URLs"

    @property
    def all_duplicates(self) -> bool:
        """Check if all URLs are duplicates."""
        return self.total_in_file > 0 and self.new_urls == 0
