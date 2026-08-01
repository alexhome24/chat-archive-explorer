from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest


class InstalledModuleSmokeTests(unittest.TestCase):
    def test_python_module_entry_point(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["CHAT_ARCHIVE_EXPLORER_DATA_DIR"] = directory
            completed = subprocess.run(
                [sys.executable, "-m", "chat_archive_explorer", "doctor", "--json"],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"healthy": true', completed.stdout)
