"""Factory for supported local import-source adapters."""

from __future__ import annotations

import zipfile
from pathlib import Path

from chat_archive_explorer.application.ports import ImportSourcePort
from chat_archive_explorer.errors import ImportSourceError
from chat_archive_explorer.infrastructure.import_sources.directory import DirectoryImportSource
from chat_archive_explorer.infrastructure.import_sources.zip import ZipImportSource


class LocalImportSourceFactory:
    """Open local directories and ZIP files through the import-source port."""

    def open(self, path: Path) -> ImportSourcePort:
        """Open a supported source or raise an actionable expected error."""

        try:
            is_symlink = path.is_symlink()
            exists = path.exists()
            is_directory = path.is_dir()
            is_file = path.is_file()
        except OSError as exc:
            raise ImportSourceError(
                "Import source metadata is not readable.",
                code="CAE-M1-SOURCE-NOT-READABLE",
                source=str(path),
                recovery="Check filesystem permissions and retry.",
            ) from exc
        if is_symlink:
            raise ImportSourceError(
                "Import source path must not be a symbolic link.",
                code="CAE-M1-ENTRY-UNSAFE-PATH",
                source=str(path),
                recovery="Select the real export directory or ZIP path and retry.",
            )
        if not exists:
            raise ImportSourceError(
                "Import source does not exist.",
                code="CAE-M1-SOURCE-NOT-FOUND",
                source=str(path),
                recovery="Check the path and select an existing export directory or ZIP file.",
            )
        if is_directory:
            return DirectoryImportSource(path)
        if not is_file:
            raise ImportSourceError(
                "Import source is not a regular directory or file.",
                code="CAE-M1-SOURCE-UNSUPPORTED",
                source=str(path),
                recovery="Select a directory or ZIP file.",
            )
        try:
            is_zip = zipfile.is_zipfile(path)
        except OSError as exc:
            raise ImportSourceError(
                "Import source is not readable.",
                code="CAE-M1-SOURCE-NOT-READABLE",
                source=str(path),
                recovery="Check file permissions and retry.",
            ) from exc
        if not is_zip:
            if path.suffix.casefold() == ".zip":
                return ZipImportSource(path)
            raise ImportSourceError(
                "Import source file is not a supported ZIP archive.",
                code="CAE-M1-SOURCE-UNSUPPORTED",
                source=str(path),
                recovery="Select the ChatGPT export directory or its ZIP archive.",
            )
        return ZipImportSource(path)
