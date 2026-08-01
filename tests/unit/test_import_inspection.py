from __future__ import annotations

import io
import unittest
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from chat_archive_explorer.application.import_inspection import inspect_export
from chat_archive_explorer.application.ports import ImportSourcePort, SourceEntry


class FakeImportSource:
    def __init__(self, paths: tuple[str, ...]) -> None:
        self._entries = tuple(SourceEntry(PurePosixPath(path), 1) for path in paths)
        self.closed = False

    @property
    def source_kind(self) -> str:
        return "fake"

    def entries(self) -> tuple[SourceEntry, ...]:
        return self._entries

    def open_entry(self, path: PurePosixPath) -> BinaryIO:
        return io.BytesIO(path.as_posix().encode())

    def fingerprint(self) -> str:
        return "fake-fingerprint"

    def close(self) -> None:
        self.closed = True


class FakeFactory:
    def __init__(self, source: FakeImportSource) -> None:
        self.source = source

    def open(self, path: Path) -> ImportSourcePort:
        return self.source


class ImportInspectionTests(unittest.TestCase):
    def test_valid_structure_builds_deterministic_inventory(self) -> None:
        source = FakeImportSource(
            ("user.json", "export_manifest.json", "conversations.json", "unexpected.bin")
        )
        report = inspect_export(Path("export"), FakeFactory(source))

        self.assertTrue(report.is_valid)
        self.assertIsNotNone(report.inventory)
        assert report.inventory is not None
        self.assertEqual(
            [entry.path.as_posix() for entry in report.inventory.entries],
            ["conversations.json", "export_manifest.json", "unexpected.bin", "user.json"],
        )
        self.assertEqual(report.required_files_missing, ())
        self.assertEqual(report.known_files_present, ("user.json",))
        self.assertTrue(source.closed)

    def test_missing_required_files_are_reported_independently(self) -> None:
        report = inspect_export(Path("export"), FakeFactory(FakeImportSource(("user.json",))))

        self.assertFalse(report.is_valid)
        self.assertEqual(
            report.required_files_missing,
            ("conversations.json", "export_manifest.json"),
        )
        missing = [
            item for item in report.diagnostics if item.code == "CAE-M1-REQUIRED-FILE-MISSING"
        ]
        self.assertEqual(len(missing), 2)
        self.assertTrue(all(item.recovery for item in missing))

    def test_report_serialization_is_stable(self) -> None:
        report = inspect_export(
            Path("export"),
            FakeFactory(FakeImportSource(("conversations.json", "export_manifest.json"))),
        )

        payload = report.to_dict()
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["source_kind"], "fake")
        self.assertEqual(payload["inventory"]["entry_count"], 2)
        self.assertEqual(payload["required_files_missing"], [])


class FakeJsonValidator:
    def validate(self, path: PurePosixPath, stream: BinaryIO):
        from chat_archive_explorer.application.import_models import LogicalFileValidation
        from chat_archive_explorer.diagnostics import Diagnostic, DiagnosticSeverity

        stream.read()
        diagnostic = Diagnostic(
            severity=DiagnosticSeverity.INFO,
            code="CAE-M1-JSON-VALID",
            message="valid",
            source=path.as_posix(),
        )
        return LogicalFileValidation(
            path=path.as_posix(),
            utf8_valid=True,
            json_valid=True,
            top_level_type="array" if path.name == "conversations.json" else "object",
            structure_valid=True,
            item_count=0,
            diagnostics=(diagnostic,),
        )


class ImportInspectionLogicalValidationTests(unittest.TestCase):
    def test_validator_runs_for_both_required_files(self) -> None:
        source = FakeImportSource(("conversations.json", "export_manifest.json"))
        report = inspect_export(Path("export"), FakeFactory(source), FakeJsonValidator())

        self.assertTrue(report.is_valid)
        self.assertEqual(
            [item.path for item in report.logical_files],
            ["conversations.json", "export_manifest.json"],
        )

    def test_validator_does_not_run_when_required_file_is_missing(self) -> None:
        source = FakeImportSource(("conversations.json",))
        report = inspect_export(Path("export"), FakeFactory(source), FakeJsonValidator())

        self.assertFalse(report.is_valid)
        self.assertEqual(report.logical_files, ())
