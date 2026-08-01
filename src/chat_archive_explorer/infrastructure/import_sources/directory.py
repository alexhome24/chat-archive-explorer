"""Read-only import source backed by a local directory."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from chat_archive_explorer.application.ports import SourceEntry
from chat_archive_explorer.errors import ImportSourceError
from chat_archive_explorer.infrastructure.import_sources.common import (
    enforce_inventory_limits,
    normalize_entry_path,
)


class DirectoryImportSource:
    """Expose regular files beneath one directory without following symlinks."""

    def __init__(self, root: Path) -> None:
        try:
            if root.is_symlink():
                raise ImportSourceError(
                    "Import source path must not be a symbolic link.",
                    code="CAE-M1-ENTRY-UNSAFE-PATH",
                    source=str(root),
                    recovery="Select the real export directory path and retry.",
                )
            self._root = root.resolve(strict=True)
        except ImportSourceError:
            raise
        except OSError as exc:
            raise ImportSourceError(
                "Import source directory is not readable.",
                code="CAE-M1-SOURCE-NOT-READABLE",
                source=str(root),
                recovery="Check directory permissions and retry.",
            ) from exc
        self._entries: dict[PurePosixPath, Path] | None = None

    @property
    def source_kind(self) -> str:
        """Return the stable source-kind identifier."""

        return "directory"

    def entries(self) -> Iterable[SourceEntry]:
        """Return deterministic metadata for all regular files under the root."""

        if self._entries is None:
            self._entries = self._scan()
        total_size = 0
        result: list[SourceEntry] = []
        sorted_entries = sorted(self._entries.items(), key=lambda item: item[0].as_posix())
        for path, physical_path in sorted_entries:
            try:
                size = physical_path.stat().st_size
            except OSError as exc:
                raise ImportSourceError(
                    f"Cannot read source entry metadata: {path.as_posix()}",
                    code="CAE-M1-SOURCE-NOT-READABLE",
                    source=str(self._root),
                    recovery="Check filesystem permissions and retry.",
                    details={"entry_path": path.as_posix()},
                ) from exc
            total_size += size
            result.append(SourceEntry(path=path, size=size))
        enforce_inventory_limits(
            entry_count=len(result), total_size=total_size, source=str(self._root)
        )
        return tuple(result)

    def open_entry(self, path: PurePosixPath) -> BinaryIO:
        """Open one inventoried entry as a binary stream."""

        if self._entries is None:
            self._entries = self._scan()
        physical_path = self._entries.get(path)
        if physical_path is None:
            raise ImportSourceError(
                f"Source entry does not exist: {path.as_posix()}",
                code="CAE-M1-SOURCE-NOT-READABLE",
                source=str(self._root),
                recovery="Rebuild the source inventory and retry.",
                details={"entry_path": path.as_posix()},
            )
        try:
            return physical_path.open("rb")
        except OSError as exc:
            raise ImportSourceError(
                f"Cannot open source entry: {path.as_posix()}",
                code="CAE-M1-SOURCE-NOT-READABLE",
                source=str(self._root),
                recovery="Check filesystem permissions and retry.",
                details={"entry_path": path.as_posix()},
            ) from exc

    def fingerprint(self) -> str:
        """Return a stable snapshot identifier derived from source metadata."""

        digest = hashlib.sha256()
        for entry in self.entries():
            digest.update(entry.path.as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(str(entry.size).encode("ascii"))
            digest.update(b"\n")
        return digest.hexdigest()

    def close(self) -> None:
        """Close the source; directory sources own no persistent handles."""

    def _scan(self) -> dict[PurePosixPath, Path]:
        entries: dict[PurePosixPath, Path] = {}
        try:
            candidates = self._root.rglob("*")
            for candidate in candidates:
                self._add_candidate(entries, candidate)
        except OSError as exc:
            raise ImportSourceError(
                "Cannot enumerate import source directory.",
                code="CAE-M1-SOURCE-NOT-READABLE",
                source=str(self._root),
                recovery="Check directory permissions and retry.",
            ) from exc
        return entries

    def _add_candidate(self, entries: dict[PurePosixPath, Path], candidate: Path) -> None:
        if candidate.is_symlink():
            raise ImportSourceError(
                f"Symbolic links are not allowed in an import source: {candidate.name}",
                code="CAE-M1-ENTRY-UNSAFE-PATH",
                source=str(self._root),
                recovery="Remove symbolic links from the selected export copy and retry.",
                details={"entry_path": str(candidate)},
            )
        if not candidate.is_file():
            return
        relative = candidate.relative_to(self._root)
        normalized = normalize_entry_path(relative.as_posix(), source=str(self._root))
        if normalized in entries:
            raise ImportSourceError(
                f"Duplicate normalized source path: {normalized.as_posix()}",
                code="CAE-M1-ENTRY-DUPLICATE-PATH",
                source=str(self._root),
                recovery="Remove duplicate paths from the source and retry.",
                details={"entry_path": normalized.as_posix()},
            )
        entries[normalized] = candidate
