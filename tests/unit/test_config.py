from __future__ import annotations

import unittest
from pathlib import Path

from chat_archive_explorer.config import AppConfig, default_data_dir
from chat_archive_explorer.errors import ConfigurationError


class AppConfigTests(unittest.TestCase):
    def test_explicit_data_directory_and_normalized_logging(self) -> None:
        config = AppConfig.from_environment(
            {
                "CHAT_ARCHIVE_EXPLORER_DATA_DIR": "~/custom-cae",
                "CHAT_ARCHIVE_EXPLORER_LOG_LEVEL": "debug",
                "CHAT_ARCHIVE_EXPLORER_LOG_FORMAT": "JSON",
            }
        )
        self.assertEqual(config.data_dir, Path("~/custom-cae").expanduser())
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.log_format, "json")

    def test_invalid_log_level_is_rejected(self) -> None:
        with self.assertRaises(ConfigurationError):
            AppConfig.from_environment({"CHAT_ARCHIVE_EXPLORER_LOG_LEVEL": "TRACE"})

    def test_macos_default_directory(self) -> None:
        home = Path("/Users/example")
        self.assertEqual(
            default_data_dir(platform="darwin", home=home),
            home / "Library" / "Application Support" / "ChatArchiveExplorer",
        )
