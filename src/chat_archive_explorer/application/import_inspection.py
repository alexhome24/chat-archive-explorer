"""Read-only structural inspection of directory and ZIP import sources."""

from __future__ import annotations

import logging
from pathlib import Path

from chat_archive_explorer.application.import_models import (
    ExportInspectionReport,
    InventoryEntry,
    SourceInventory,
)
from chat_archive_explorer.application.ports import (
    ImportSourceFactoryPort,
    ImportSourcePort,
)
from chat_archive_explorer.diagnostics import Diagnostic, DiagnosticSeverity
from chat_archive_explorer.errors import ImportSourceError

logger = logging.getLogger(__name__)

REQUIRED_EXPORT_FILES = ("conversations.json", "export_manifest.json")
KNOWN_OPTIONAL_EXPORT_FILES = (
    "ads.json",
    "chat.html",
    "conversation_asset_file_names.json",
    "library_files.json",
    "shared_conversations.json",
    "user.json",
    "user_settings.json",
)


def inspect_export(
    source_path: Path, source_factory: ImportSourceFactoryPort
) -> ExportInspectionReport:
    """Inspect source structure without parsing JSON or modifying source files."""

    diagnostics: list[Diagnostic] = []
    source: ImportSourcePort | None = None
    source_kind: str | None = None
    fingerprint: str | None = None
    inventory: SourceInventory | None = None

    try:
        source = source_factory.open(source_path)
        source_kind = source.source_kind
        fingerprint = source.fingerprint()
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.INFO,
                code="CAE-M1-SOURCE-OPENED",
                message="Import source opened in read-only mode.",
                source=str(source_path),
                details={"source_kind": source_kind},
            )
        )
        logger.info("import source opened", extra={"event": "CAE-M1-SOURCE-OPENED"})

        entries = tuple(
            sorted(
                (
                    InventoryEntry(
                        path=entry.path,
                        size=entry.size,
                        compressed_size=entry.compressed_size,
                    )
                    for entry in source.entries()
                ),
                key=lambda item: item.path.as_posix(),
            )
        )
        inventory = SourceInventory(entries=entries)
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.INFO,
                code="CAE-M1-INVENTORY-COMPLETE",
                message="Source inventory was built successfully.",
                source=str(source_path),
                details={
                    "entry_count": inventory.entry_count,
                    "total_size": inventory.total_size,
                },
            )
        )
        logger.info("source inventory complete", extra={"event": "CAE-M1-INVENTORY-COMPLETE"})
    except ImportSourceError as exc:
        diagnostics.append(exc.to_diagnostic())
    finally:
        if source is not None:
            source.close()

    paths = {entry.path.as_posix() for entry in inventory.entries} if inventory else set()
    required_present = (
        tuple(path for path in REQUIRED_EXPORT_FILES if path in paths) if inventory else ()
    )
    required_missing = (
        tuple(path for path in REQUIRED_EXPORT_FILES if path not in paths) if inventory else ()
    )
    known_present = (
        tuple(path for path in KNOWN_OPTIONAL_EXPORT_FILES if path in paths) if inventory else ()
    )

    for path in required_missing:
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="CAE-M1-REQUIRED-FILE-MISSING",
                message=f"Required export file is missing: {path}",
                recovery=(
                    "Select the root directory or ZIP of a complete ChatGPT data export. "
                    "Do not select an extracted subdirectory."
                ),
                source=str(source_path),
                entity_id=path,
                details={"path": path},
            )
        )

    if inventory is not None and not required_missing:
        diagnostics.append(
            Diagnostic(
                severity=DiagnosticSeverity.INFO,
                code="CAE-M1-SOURCE-STRUCTURE-VALID",
                message="Source contains all files required for structural inspection.",
                source=str(source_path),
                details={"required_files": list(REQUIRED_EXPORT_FILES)},
            )
        )

    return ExportInspectionReport(
        source=str(source_path),
        source_kind=source_kind,
        fingerprint=fingerprint,
        inventory=inventory,
        required_files=REQUIRED_EXPORT_FILES,
        required_files_present=required_present,
        required_files_missing=required_missing,
        known_files_present=known_present,
        diagnostics=tuple(diagnostics),
    )
