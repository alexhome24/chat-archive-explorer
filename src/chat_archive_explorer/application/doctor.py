"""Milestone M0 self-check application service."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from chat_archive_explorer.application.ports import RuntimeFilesystemPort
from chat_archive_explorer.config import AppConfig
from chat_archive_explorer.diagnostics import Diagnostic, DiagnosticSeverity
from chat_archive_explorer.version import SCHEMA_VERSION, __version__

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Complete result of a local environment self-check."""

    application_version: str
    schema_version: int
    data_dir: Path
    diagnostics: tuple[Diagnostic, ...]

    @property
    def is_healthy(self) -> bool:
        """Return true when no error or critical diagnostic exists."""

        return all(
            item.severity not in {DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL}
            for item in self.diagnostics
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the report for stable JSON output."""

        return {
            "application": "chat-archive-explorer",
            "application_version": self.application_version,
            "schema_version": self.schema_version,
            "data_dir": str(self.data_dir),
            "healthy": self.is_healthy,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def run_doctor(config: AppConfig, filesystem: RuntimeFilesystemPort) -> DoctorReport:
    """Create required directories and verify the local runtime environment."""

    diagnostics: list[Diagnostic] = []
    for directory, code in (
        (config.data_dir, "CAE-M0-DATA-DIR-OK"),
        (config.logs_dir, "CAE-M0-LOGS-DIR-OK"),
        (config.temp_dir, "CAE-M0-TEMP-DIR-OK"),
        (config.config_dir, "CAE-M0-CONFIG-DIR-OK"),
    ):
        filesystem.ensure_directory(directory)
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.INFO,
                code=code,
                message="Directory exists and is writable.",
                details={"directory": str(directory)},
            )
        )
        logger.info("self-check directory passed", extra={"event": code})

    diagnostics.append(
        Diagnostic(
            severity=DiagnosticSeverity.INFO,
            code="CAE-M0-OFFLINE-RUNTIME",
            message="Runtime configuration has no required network dependency.",
        )
    )
    return DoctorReport(
        application_version=__version__,
        schema_version=SCHEMA_VERSION,
        data_dir=config.data_dir,
        diagnostics=tuple(diagnostics),
    )
