"""Primary architecture contracts required by future milestones."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Protocol, runtime_checkable

from chat_archive_explorer.diagnostics import Diagnostic


@dataclass(frozen=True, slots=True)
class SourceEntry:
    """Read-only metadata for one entry exposed by an import source."""

    path: PurePosixPath
    size: int
    compressed_size: int | None = None


@runtime_checkable
class ImportSourcePort(Protocol):
    """Read-only access to a directory or archive source."""

    @property
    def source_kind(self) -> str: ...

    def entries(self) -> Iterable[SourceEntry]: ...

    def open_entry(self, path: PurePosixPath) -> BinaryIO: ...

    def fingerprint(self) -> str: ...

    def close(self) -> None: ...


@runtime_checkable
class ImportSourceFactoryPort(Protocol):
    """Open a supported import source without exposing adapter details."""

    def open(self, path: Path) -> ImportSourcePort: ...


@runtime_checkable
class BlobStorePort(Protocol):
    """Immutable content-addressed blob operations."""

    def contains(self, sha256: str) -> bool: ...

    def open(self, sha256: str) -> BinaryIO: ...


@runtime_checkable
class RuntimeFilesystemPort(Protocol):
    """Minimal filesystem operations required by application self-checks."""

    def ensure_directory(self, path: Path) -> None: ...


@runtime_checkable
class DiagnosticSink(Protocol):
    """Persistence-neutral destination for structured diagnostics."""

    def record(self, diagnostic: Diagnostic) -> None: ...
