"""Read-only structural and logical inspection of import sources."""

from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath

from chat_archive_explorer.application.import_models import (
    ExportInspectionReport,
    InventoryEntry,
    LogicalFileValidation,
    SourceInventory,
)
from chat_archive_explorer.application.ports import (
    ImportSourceFactoryPort,
    ImportSourcePort,
    LogicalJsonValidatorPort,
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
    source_path: Path,
    source_factory: ImportSourceFactoryPort,
    json_validator: LogicalJsonValidatorPort | None = None,
) -> ExportInspectionReport:
    """Inspect source structure and, when provided, required logical JSON files."""

    diagnostics: list[Diagnostic] = []
    logical_files: list[LogicalFileValidation] = []
    source: ImportSourcePort | None = None
    source_kind: str | None = None
    fingerprint: str | None = None
    inventory: SourceInventory | None = None
    required_present: tuple[str, ...] = ()
    required_missing: tuple[str, ...] = ()
    known_present: tuple[str, ...] = ()

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

        inventory = _build_inventory(source, source_path, diagnostics)
        paths = {entry.path.as_posix() for entry in inventory.entries}
        required_present = tuple(path for path in REQUIRED_EXPORT_FILES if path in paths)
        required_missing = tuple(path for path in REQUIRED_EXPORT_FILES if path not in paths)
        known_present = tuple(path for path in KNOWN_OPTIONAL_EXPORT_FILES if path in paths)

        _append_required_file_diagnostics(source_path, required_missing, diagnostics)
        if not required_missing:
            diagnostics.append(
                Diagnostic(
                    severity=DiagnosticSeverity.INFO,
                    code="CAE-M1-SOURCE-STRUCTURE-VALID",
                    message="Source contains all files required for structural inspection.",
                    source=str(source_path),
                    details={"required_files": list(REQUIRED_EXPORT_FILES)},
                )
            )
            if json_validator is not None:
                logical_files.extend(
                    _validate_required_json_files(source, json_validator, source_path, diagnostics)
                )
    except ImportSourceError as exc:
        diagnostics.append(exc.to_diagnostic())
    finally:
        if source is not None:
            source.close()

    return ExportInspectionReport(
        source=str(source_path),
        source_kind=source_kind,
        fingerprint=fingerprint,
        inventory=inventory,
        required_files=REQUIRED_EXPORT_FILES,
        required_files_present=required_present,
        required_files_missing=required_missing,
        known_files_present=known_present,
        logical_files=tuple(logical_files),
        diagnostics=tuple(diagnostics),
    )


def _build_inventory(
    source: ImportSourcePort,
    source_path: Path,
    diagnostics: list[Diagnostic],
) -> SourceInventory:
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
    return inventory


def _append_required_file_diagnostics(
    source_path: Path,
    required_missing: tuple[str, ...],
    diagnostics: list[Diagnostic],
) -> None:
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


def _validate_required_json_files(
    source: ImportSourcePort,
    validator: LogicalJsonValidatorPort,
    source_path: Path,
    diagnostics: list[Diagnostic],
) -> tuple[LogicalFileValidation, ...]:
    results: list[LogicalFileValidation] = []
    for path_text in REQUIRED_EXPORT_FILES:
        path = PurePosixPath(path_text)
        try:
            with source.open_entry(path) as stream:
                result = validator.validate(path, stream)
        except ImportSourceError as exc:
            diagnostics.append(exc.to_diagnostic())
            continue
        except OSError as exc:
            diagnostics.append(
                Diagnostic(
                    severity=DiagnosticSeverity.ERROR,
                    code="CAE-M1-JSON-OPEN-FAILED",
                    message=f"Required JSON file could not be read: {path_text}",
                    recovery="Check source permissions or ZIP integrity and retry.",
                    source=str(source_path),
                    entity_id=path_text,
                    details={"error_type": type(exc).__name__},
                )
            )
            continue
        results.append(result)
        diagnostics.extend(result.diagnostics)
    return tuple(results)
