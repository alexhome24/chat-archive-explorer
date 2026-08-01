"""Safe filesystem primitives used by application infrastructure."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from chat_archive_explorer.errors import ConfigurationError, StorageError


class LocalFilesystem:
    """Local filesystem adapter for application runtime operations."""

    def ensure_directory(self, path: Path) -> None:
        """Create a directory and verify that it is writable."""

        ensure_directory(path)


def ensure_directory(path: Path) -> None:
    """Create a directory and verify that it is writable."""

    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(f"Cannot create directory: {path}") from exc
    if not path.is_dir():
        raise ConfigurationError(f"Configured path is not a directory: {path}")

    try:
        with tempfile.NamedTemporaryFile(dir=path, prefix=".write-check-", delete=True) as probe:
            probe.flush()
    except OSError as exc:
        raise ConfigurationError(f"Directory is not writable: {path}") from exc


def atomic_write_bytes(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    """Atomically replace a file with bytes written in the same directory."""

    ensure_directory(path.parent)
    temporary_path: Path | None = None
    try:
        descriptor, raw_temporary_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary_path = Path(raw_temporary_path)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    except OSError as exc:
        raise StorageError(f"Atomic write failed for: {path}") from exc
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Atomically replace a text file using an explicit encoding."""

    atomic_write_bytes(path, text.encode(encoding))
