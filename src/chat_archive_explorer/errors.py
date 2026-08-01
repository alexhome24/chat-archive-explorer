"""Project exception hierarchy and process exit codes."""

from __future__ import annotations

from collections.abc import Mapping
from enum import IntEnum
from typing import Any

from chat_archive_explorer.diagnostics import Diagnostic, DiagnosticSeverity


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

    exit_code = ExitCode.VALIDATION_ERROR


class ImportSourceError(ImportError):
    """Expected failure while opening or inventorying an import source."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        source: str,
        recovery: str | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.source = source
        self.recovery = recovery
        self.details = dict(details or {})

    def to_diagnostic(self) -> Diagnostic:
        """Convert the expected failure to a stable user-facing diagnostic."""

        return Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code=self.code,
            message=str(self),
            recovery=self.recovery,
            source=self.source,
            details=self.details,
        )


class StorageError(ChatArchiveError):
    """Raised for durable metadata storage failures."""


class BlobError(ChatArchiveError):
    """Raised for immutable blob storage failures."""


class SearchError(ChatArchiveError):
    """Raised for search indexing or query failures."""


class ExportError(ChatArchiveError):
    """Raised for archive or conversation export failures."""
