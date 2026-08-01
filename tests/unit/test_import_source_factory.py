from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from chat_archive_explorer.errors import ImportSourceError
from chat_archive_explorer.infrastructure.import_sources import (
    DirectoryImportSource,
    LocalImportSourceFactory,
    ZipImportSource,
)


class ImportSourceFactoryTests(unittest.TestCase):
    def test_opens_directory_and_zip(self) -> None:
        factory = LocalImportSourceFactory()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIsInstance(factory.open(root), DirectoryImportSource)
            archive_path = root / "export.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("conversations.json", "[]")
            source = factory.open(archive_path)
            try:
                self.assertIsInstance(source, ZipImportSource)
            finally:
                source.close()

    def test_invalid_zip_has_specific_diagnostic_code(self) -> None:
        factory = LocalImportSourceFactory()
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "broken.zip"
            archive_path.write_bytes(b"not a zip")
            with self.assertRaises(ImportSourceError) as invalid:
                factory.open(archive_path)
            self.assertEqual(invalid.exception.code, "CAE-M1-ZIP-INVALID")

    def test_missing_and_plain_file_have_actionable_codes(self) -> None:
        factory = LocalImportSourceFactory()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ImportSourceError) as missing:
                factory.open(root / "missing")
            self.assertEqual(missing.exception.code, "CAE-M1-SOURCE-NOT-FOUND")

            plain = root / "plain.txt"
            plain.write_text("not a zip", encoding="utf-8")
            with self.assertRaises(ImportSourceError) as unsupported:
                factory.open(plain)
            self.assertEqual(unsupported.exception.code, "CAE-M1-SOURCE-UNSUPPORTED")
