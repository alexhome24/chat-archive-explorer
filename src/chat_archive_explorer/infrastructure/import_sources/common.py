"""Shared safety rules for local import-source adapters."""

from __future__ import annotations

from pathlib import PurePosixPath

from chat_archive_explorer.errors import ImportSourceError

MAX_ENTRY_COUNT = 250_000
MAX_TOTAL_UNCOMPRESSED_SIZE = 100 * 1024 * 1024 * 1024


def normalize_entry_path(raw_path: str, *, source: str) -> PurePosixPath:
    """Normalize an archive-style path and reject traversal or absolute paths."""

    candidate = raw_path.replace("\\", "/")
    path = PurePosixPath(candidate)
    if not candidate or path.is_absolute() or any(part == ".." for part in path.parts):
        raise ImportSourceError(
            f"Unsafe source entry path: {raw_path}",
            code="CAE-M1-ENTRY-UNSAFE-PATH",
            source=source,
            recovery="Use an export archive that contains only relative paths without '..'.",
            details={"entry_path": raw_path},
        )
    normalized_parts = tuple(part for part in path.parts if part not in {"", "."})
    if not normalized_parts or ":" in normalized_parts[0]:
        raise ImportSourceError(
            f"Unsafe source entry path: {raw_path}",
            code="CAE-M1-ENTRY-UNSAFE-PATH",
            source=source,
            recovery="Use an export archive that contains portable relative paths.",
            details={"entry_path": raw_path},
        )
    return PurePosixPath(*normalized_parts)


def enforce_inventory_limits(*, entry_count: int, total_size: int, source: str) -> None:
    """Reject source metadata that exceeds conservative inventory safety limits."""

    if entry_count > MAX_ENTRY_COUNT or total_size > MAX_TOTAL_UNCOMPRESSED_SIZE:
        raise ImportSourceError(
            "Import source exceeds configured inventory safety limits.",
            code="CAE-M1-SOURCE-LIMIT-EXCEEDED",
            source=source,
            recovery="Use a complete export within supported size limits or split it externally.",
            details={
                "entry_count": entry_count,
                "entry_count_limit": MAX_ENTRY_COUNT,
                "total_size": total_size,
                "total_size_limit": MAX_TOTAL_UNCOMPRESSED_SIZE,
            },
        )
