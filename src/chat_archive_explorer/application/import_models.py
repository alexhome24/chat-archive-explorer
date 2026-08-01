"""Application DTOs for read-only import-source inspection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from chat_archive_explorer.diagnostics import Diagnostic, DiagnosticSeverity


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    """Normalized metadata for one physical entry in an import source."""

    path: PurePosixPath
    size: int
    compressed_size: int | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the entry using stable machine-readable field names."""

        payload: dict[str, object] = {"path": self.path.as_posix(), "size": self.size}
        if self.compressed_size is not None:
            payload["compressed_size"] = self.compressed_size
        return payload


@dataclass(frozen=True, slots=True)
class SourceInventory:
    """Deterministic inventory of all regular files exposed by a source."""

    entries: tuple[InventoryEntry, ...]

    @property
    def entry_count(self) -> int:
        """Return the number of physical file entries."""

        return len(self.entries)

    @property
    def total_size(self) -> int:
        """Return the sum of uncompressed entry sizes."""

        return sum(entry.size for entry in self.entries)

    def to_dict(self) -> dict[str, object]:
        """Serialize the inventory in deterministic path order."""

        return {
            "entry_count": self.entry_count,
            "total_size": self.total_size,
            "entries": [entry.to_dict() for entry in self.entries],
        }


@dataclass(frozen=True, slots=True)
class LogicalFileValidation:
    """Validation result for one required logical JSON file."""

    path: str
    utf8_valid: bool
    json_valid: bool
    top_level_type: str | None
    structure_valid: bool
    item_count: int | None
    diagnostics: tuple[Diagnostic, ...]

    @property
    def is_valid(self) -> bool:
        """Return true when all validation stages succeeded."""

        return self.utf8_valid and self.json_valid and self.structure_valid

    def to_dict(self) -> dict[str, Any]:
        """Serialize the validation result using stable field names."""

        return {
            "path": self.path,
            "valid": self.is_valid,
            "utf8_valid": self.utf8_valid,
            "json_valid": self.json_valid,
            "top_level_type": self.top_level_type,
            "structure_valid": self.structure_valid,
            "item_count": self.item_count,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


@dataclass(frozen=True, slots=True)
class ExportInspectionReport:
    """Complete structural inspection result for one directory or ZIP source."""

    source: str
    source_kind: str | None
    fingerprint: str | None
    inventory: SourceInventory | None
    required_files: tuple[str, ...]
    required_files_present: tuple[str, ...]
    required_files_missing: tuple[str, ...]
    known_files_present: tuple[str, ...]
    logical_files: tuple[LogicalFileValidation, ...]
    diagnostics: tuple[Diagnostic, ...]

    @property
    def is_valid(self) -> bool:
        """Return true when inspection produced no error diagnostic."""

        return all(
            diagnostic.severity not in {DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL}
            for diagnostic in self.diagnostics
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report for stable JSON output."""

        return {
            "source": self.source,
            "source_kind": self.source_kind,
            "fingerprint": self.fingerprint,
            "valid": self.is_valid,
            "inventory": self.inventory.to_dict() if self.inventory is not None else None,
            "required_files": list(self.required_files),
            "required_files_present": list(self.required_files_present),
            "required_files_missing": list(self.required_files_missing),
            "known_files_present": list(self.known_files_present),
            "logical_files": [item.to_dict() for item in self.logical_files],
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }
