from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from chat_archive_explorer.cli.main import run
from chat_archive_explorer.errors import ExitCode


class CliIntegrationTests(unittest.TestCase):
    def test_doctor_json_is_runnable_and_successful(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            stdout = io.StringIO()
            with (
                patch.dict(
                    os.environ,
                    {
                        "CHAT_ARCHIVE_EXPLORER_DATA_DIR": directory,
                        "CHAT_ARCHIVE_EXPLORER_LOG_LEVEL": "CRITICAL",
                    },
                    clear=False,
                ),
                contextlib.redirect_stdout(stdout),
            ):
                exit_code = run(["doctor", "--json"])

            self.assertEqual(exit_code, ExitCode.SUCCESS)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["healthy"])
            self.assertEqual(payload["schema_version"], 0)
            self.assertGreaterEqual(len(payload["diagnostics"]), 5)

    def test_configuration_error_has_stable_exit_code_and_no_traceback(self) -> None:
        stderr = io.StringIO()
        with (
            patch.dict(
                os.environ,
                {"CHAT_ARCHIVE_EXPLORER_LOG_LEVEL": "INVALID"},
                clear=False,
            ),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = run(["doctor"])
        self.assertEqual(exit_code, ExitCode.CONFIGURATION_ERROR)
        self.assertNotIn("Traceback", stderr.getvalue())
