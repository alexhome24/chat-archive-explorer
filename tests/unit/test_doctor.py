from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from chat_archive_explorer.application.doctor import run_doctor
from chat_archive_explorer.config import AppConfig
from chat_archive_explorer.filesystem import LocalFilesystem


class DoctorServiceTests(unittest.TestCase):
    def test_doctor_creates_required_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory) / "application-data"
            report = run_doctor(AppConfig(data_dir=data_dir), LocalFilesystem())
            self.assertTrue(report.is_healthy)
            self.assertTrue(data_dir.is_dir())
            self.assertTrue((data_dir / "logs").is_dir())
            self.assertTrue((data_dir / "tmp").is_dir())
            self.assertTrue((data_dir / "config").is_dir())
            self.assertEqual(report.schema_version, 0)
