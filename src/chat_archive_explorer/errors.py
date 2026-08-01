"""Project exception hierarchy and process exit codes."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """Stable command-line process exit codes."""

    SUCCESS = 0
    USAGE = 2
    CONFIGURATION_ERROR = 10
    VALIDATION_ERROR = 20
    INTERNAL_ERROR = 70


class ChatArchiveError(Exception):
    """Base class for expected application failures."""

    exit_code = ExitCode.INTERNAL_ERROR


class ConfigurationError(ChatArchiveError):
    """Raised when application configuration is invalid or unusable."""

    exit_code = ExitCode.CONFIGURATION_ERROR


class ValidationError(ChatArchiveError):
    """Raised when a requested operation fails a validation rule."""

    exit_code = ExitCode.VALIDATION_ERROR


class ImportError(ChatArchiveError):
    """Raised for import pipeline failures."""


class StorageError(ChatArchiveError):
    """Raised for durable metadata storage failures."""


class BlobError(ChatArchiveError):
    """Raised for immutable blob storage failures."""


class SearchError(ChatArchiveError):
    """Raised for search indexing or query failures."""


class ExportError(ChatArchiveError):
    """Raised for archive or conversation export failures."""
