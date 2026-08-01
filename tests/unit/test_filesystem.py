from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from chat_archive_explorer.filesystem import atomic_write_bytes, atomic_write_text


class AtomicWriteTests(unittest.TestCase):
    def test_atomic_text_write_replaces_existing_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "nested" / "state.txt"
            atomic_write_text(destination, "first")
            atomic_write_text(destination, "second")
            self.assertEqual(destination.read_text(encoding="utf-8"), "second")
            self.assertEqual(list(destination.parent.glob(f".{destination.name}.*")), [])

    def test_atomic_bytes_write_preserves_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "payload.bin"
            payload = b"\x00\xff\x10"
            atomic_write_bytes(destination, payload)
            self.assertEqual(destination.read_bytes(), payload)
