from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
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

    def test_inspect_export_directory_and_zip_return_equivalent_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            export_dir = root / "export"
            export_dir.mkdir()
            (export_dir / "conversations.json").write_text(
                '[{"id":"conversation-1","mapping":{}}]', encoding="utf-8"
            )
            (export_dir / "export_manifest.json").write_text(
                '{"export_files":[]}', encoding="utf-8"
            )
            (export_dir / "user.json").write_text("{}", encoding="utf-8")
            archive_path = root / "export.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for path in export_dir.iterdir():
                    archive.write(path, arcname=path.name)

            payloads = []
            for source in (export_dir, archive_path):
                stdout = io.StringIO()
                with (
                    patch.dict(
                        os.environ,
                        {"CHAT_ARCHIVE_EXPLORER_LOG_LEVEL": "CRITICAL"},
                        clear=False,
                    ),
                    contextlib.redirect_stdout(stdout),
                ):
                    exit_code = run(["inspect-export", str(source), "--json"])
                self.assertEqual(exit_code, ExitCode.SUCCESS)
                payloads.append(json.loads(stdout.getvalue()))

            self.assertTrue(all(payload["valid"] for payload in payloads))
            self.assertEqual(
                payloads[0]["required_files_present"],
                payloads[1]["required_files_present"],
            )
            self.assertEqual(payloads[0]["known_files_present"], ["user.json"])
            self.assertEqual(payloads[0]["inventory"]["entry_count"], 3)
            self.assertEqual(payloads[1]["inventory"]["entry_count"], 3)
            self.assertEqual(payloads[0]["logical_files"], payloads[1]["logical_files"])

    def test_inspect_export_reports_missing_required_file_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "conversations.json").write_text("[]", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.dict(
                    os.environ,
                    {"CHAT_ARCHIVE_EXPLORER_LOG_LEVEL": "CRITICAL"},
                    clear=False,
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = run(["inspect-export", str(root), "--json"])

            self.assertEqual(exit_code, ExitCode.VALIDATION_ERROR)
            payload = json.loads(stdout.getvalue())
            self.assertFalse(payload["valid"])
            self.assertEqual(payload["required_files_missing"], ["export_manifest.json"])
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_inspect_export_reports_missing_source_as_json(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = run(["inspect-export", "/definitely/missing/export", "--json"])

        self.assertEqual(exit_code, ExitCode.VALIDATION_ERROR)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["valid"])
        self.assertEqual(payload["diagnostics"][0]["code"], "CAE-M1-SOURCE-NOT-FOUND")
        self.assertEqual(payload["required_files_missing"], [])

    def test_inspect_export_rejects_invalid_json_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "conversations.json").write_text("[{", encoding="utf-8")
            (root / "export_manifest.json").write_text('{"export_files":[]}', encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.dict(
                    os.environ,
                    {"CHAT_ARCHIVE_EXPLORER_LOG_LEVEL": "CRITICAL"},
                    clear=False,
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                exit_code = run(["inspect-export", str(root), "--json"])

            self.assertEqual(exit_code, ExitCode.VALIDATION_ERROR)
            payload = json.loads(stdout.getvalue())
            self.assertFalse(payload["valid"])
            self.assertEqual(
                payload["logical_files"][0]["diagnostics"][0]["code"],
                "CAE-M1-JSON-SYNTAX-ERROR",
            )
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_inspect_export_rejects_invalid_minimal_conversation_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "conversations.json").write_text(
                '[{"id":"conversation-1","mapping":[]}]', encoding="utf-8"
            )
            (root / "export_manifest.json").write_text('{"export_files":[]}', encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.dict(
                    os.environ,
                    {"CHAT_ARCHIVE_EXPLORER_LOG_LEVEL": "CRITICAL"},
                    clear=False,
                ),
                contextlib.redirect_stdout(stdout),
            ):
                exit_code = run(["inspect-export", str(root), "--json"])

            self.assertEqual(exit_code, ExitCode.VALIDATION_ERROR)
            payload = json.loads(stdout.getvalue())
            codes = [item["code"] for item in payload["diagnostics"]]
            self.assertIn("CAE-M1-CONVERSATIONS-STRUCTURE-INVALID", codes)
