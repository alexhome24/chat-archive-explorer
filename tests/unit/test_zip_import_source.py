from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath

from chat_archive_explorer.errors import ImportSourceError
from chat_archive_explorer.infrastructure.import_sources import ZipImportSource


class ZipImportSourceTests(unittest.TestCase):
    def test_lists_and_opens_entries_without_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "export.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("nested/value.bin", b"value")
            source = ZipImportSource(archive_path)
            try:
                entries = tuple(source.entries())
                self.assertEqual(entries[0].path, PurePosixPath("nested/value.bin"))
                self.assertEqual(entries[0].size, 5)
                with source.open_entry(entries[0].path) as stream:
                    self.assertEqual(stream.read(), b"value")
                self.assertFalse((Path(directory) / "nested").exists())
            finally:
                source.close()

    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../escape.txt", b"value")
            source = ZipImportSource(archive_path)
            try:
                with self.assertRaises(ImportSourceError) as context:
                    tuple(source.entries())
                self.assertEqual(context.exception.code, "CAE-M1-ENTRY-UNSAFE-PATH")
            finally:
                source.close()

    def test_rejects_duplicate_normalized_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "duplicate.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("folder/./value.txt", b"first")
                archive.writestr("folder/value.txt", b"second")
            source = ZipImportSource(archive_path)
            try:
                with self.assertRaises(ImportSourceError) as context:
                    tuple(source.entries())
                self.assertEqual(context.exception.code, "CAE-M1-ENTRY-DUPLICATE-PATH")
            finally:
                source.close()
