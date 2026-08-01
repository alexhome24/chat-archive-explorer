from __future__ import annotations

import tempfile
import unittest
from pathlib import Path, PurePosixPath

from chat_archive_explorer.errors import ImportSourceError
from chat_archive_explorer.infrastructure.import_sources import DirectoryImportSource


class DirectoryImportSourceTests(unittest.TestCase):
    def test_lists_recursively_and_opens_binary_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "nested" / "value.bin").write_bytes(b"value")
            source = DirectoryImportSource(root)

            entries = tuple(source.entries())
            self.assertEqual(entries[0].path, PurePosixPath("nested/value.bin"))
            self.assertEqual(entries[0].size, 5)
            with source.open_entry(entries[0].path) as stream:
                self.assertEqual(stream.read(), b"value")

    def test_rejects_symbolic_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.txt"
            target.write_text("value", encoding="utf-8")
            link = root / "link.txt"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable on this platform")

            with self.assertRaises(ImportSourceError) as context:
                tuple(DirectoryImportSource(root).entries())
            self.assertEqual(context.exception.code, "CAE-M1-ENTRY-UNSAFE-PATH")
