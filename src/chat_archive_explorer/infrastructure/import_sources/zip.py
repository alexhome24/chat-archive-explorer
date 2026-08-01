"""Read-only import source backed by a local ZIP archive."""

from __future__ import annotations

import hashlib
import stat
import zipfile
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import BinaryIO, cast

from chat_archive_explorer.application.ports import SourceEntry
from chat_archive_explorer.errors import ImportSourceError
from chat_archive_explorer.infrastructure.import_sources.common import (
    enforce_inventory_limits,
    normalize_entry_path,
)


class ZipImportSource:
    """Inventory and stream ZIP entries without extracting the archive."""

    def __init__(self, path: Path) -> None:
        self._path = path
        try:
            self._archive = zipfile.ZipFile(path, mode="r")
        except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
            raise ImportSourceError(
                "ZIP source is invalid or unreadable.",
                code="CAE-M1-ZIP-INVALID",
                source=str(path),
                recovery="Select an intact ZIP produced by the ChatGPT export process.",
            ) from exc
        self._entries: dict[PurePosixPath, zipfile.ZipInfo] | None = None

    @property
    def source_kind(self) -> str:
        """Return the stable source-kind identifier."""

        return "zip"

    def entries(self) -> Iterable[SourceEntry]:
        """Return deterministic central-directory metadata for regular files."""

        if self._entries is None:
            self._entries = self._scan()
        result = tuple(
            SourceEntry(
                path=path,
                size=info.file_size,
                compressed_size=info.compress_size,
            )
            for path, info in sorted(self._entries.items(), key=lambda item: item[0].as_posix())
        )
        enforce_inventory_limits(
            entry_count=len(result),
            total_size=sum(entry.size for entry in result),
            source=str(self._path),
        )
        return result

    def open_entry(self, path: PurePosixPath) -> BinaryIO:
        """Open one ZIP entry as a binary stream without extracting it."""

        if self._entries is None:
            self._entries = self._scan()
        info = self._entries.get(path)
        if info is None:
            raise ImportSourceError(
                f"Source entry does not exist: {path.as_posix()}",
                code="CAE-M1-SOURCE-NOT-READABLE",
                source=str(self._path),
                recovery="Rebuild the source inventory and retry.",
                details={"entry_path": path.as_posix()},
            )
        try:
            return cast(BinaryIO, self._archive.open(info, mode="r"))
        except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
            raise ImportSourceError(
                f"Cannot open ZIP entry: {path.as_posix()}",
                code="CAE-M1-SOURCE-NOT-READABLE",
                source=str(self._path),
                recovery="Verify archive integrity and retry.",
                details={"entry_path": path.as_posix()},
            ) from exc

    def fingerprint(self) -> str:
        """Return a stable snapshot identifier derived from ZIP metadata."""

        digest = hashlib.sha256()
        for entry in self.entries():
            digest.update(entry.path.as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(str(entry.size).encode("ascii"))
            digest.update(b"\0")
            digest.update(str(entry.compressed_size).encode("ascii"))
            digest.update(b"\n")
        return digest.hexdigest()

    def close(self) -> None:
        """Close the underlying ZIP handle idempotently."""

        self._archive.close()

    def _scan(self) -> dict[PurePosixPath, zipfile.ZipInfo]:
        entries: dict[PurePosixPath, zipfile.ZipInfo] = {}
        try:
            infos = self._archive.infolist()
        except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
            raise ImportSourceError(
                "Cannot enumerate ZIP source entries.",
                code="CAE-M1-ZIP-INVALID",
                source=str(self._path),
                recovery="Verify archive integrity and retry.",
            ) from exc
        for info in infos:
            if info.is_dir():
                continue
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise ImportSourceError(
                    f"Symbolic links are not allowed in ZIP sources: {info.filename}",
                    code="CAE-M1-ENTRY-UNSAFE-PATH",
                    source=str(self._path),
                    recovery="Use an export archive without symbolic links.",
                    details={"entry_path": info.filename},
                )
            normalized = normalize_entry_path(info.filename, source=str(self._path))
            if normalized in entries:
                raise ImportSourceError(
                    f"Duplicate normalized ZIP path: {normalized.as_posix()}",
                    code="CAE-M1-ENTRY-DUPLICATE-PATH",
                    source=str(self._path),
                    recovery="Use an archive without duplicate file paths.",
                    details={"entry_path": normalized.as_posix()},
                )
            entries[normalized] = info
        return entries
