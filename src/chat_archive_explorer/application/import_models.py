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
    diagnostics: tuple[Diagnostic, ...]

    @property
    def is_valid(self) -> bool:
        """Return true when structural inspection produced no error diagnostic."""

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
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }
