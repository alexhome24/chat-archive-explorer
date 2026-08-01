from __future__ import annotations

import io
import unittest
from pathlib import PurePosixPath

from chat_archive_explorer.importers.openai_export import OpenAIJsonValidator


class OpenAIJsonValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = OpenAIJsonValidator()

    def validate(self, name: str, payload: bytes):
        return self.validator.validate(PurePosixPath(name), io.BytesIO(payload))

    def test_manifest_validates_minimal_structure(self) -> None:
        result = self.validate(
            "export_manifest.json",
            b'{"export_files":[{"path":"conversations.json","size_bytes":2}],"extra":true}',
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.top_level_type, "object")
        self.assertEqual(result.item_count, 1)

    def test_manifest_rejects_wrong_top_level_type(self) -> None:
        result = self.validate("export_manifest.json", b"[]")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.diagnostics[0].code, "CAE-M1-JSON-TOP-LEVEL-TYPE")

    def test_manifest_requires_export_files_array(self) -> None:
        for payload in (b"{}", b'{"export_files":{}}'):
            with self.subTest(payload=payload):
                result = self.validate("export_manifest.json", payload)
                self.assertFalse(result.is_valid)
                self.assertEqual(result.diagnostics[0].code, "CAE-M1-MANIFEST-STRUCTURE-INVALID")

    def test_manifest_requires_object_entries(self) -> None:
        result = self.validate("export_manifest.json", b'{"export_files":["bad"]}')
        self.assertFalse(result.is_valid)
        self.assertEqual(result.diagnostics[0].details["record_index"], 0)

    def test_conversations_accepts_id_or_conversation_id(self) -> None:
        payloads = (
            b'[{"id":"one","mapping":{}}]',
            b'[{"conversation_id":"two","mapping":{}}]',
            b'[{"id":"one","conversation_id":"two","mapping":{}}]',
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                result = self.validate("conversations.json", payload)
                self.assertTrue(result.is_valid)
                self.assertEqual(result.item_count, 1)

    def test_conversations_accepts_empty_array(self) -> None:
        result = self.validate("conversations.json", b"[]")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.item_count, 0)

    def test_conversations_rejects_missing_identifier(self) -> None:
        result = self.validate("conversations.json", b'[{"mapping":{}}]')
        self.assertFalse(result.is_valid)
        diagnostic = result.diagnostics[0]
        self.assertEqual(diagnostic.code, "CAE-M1-CONVERSATIONS-STRUCTURE-INVALID")
        self.assertEqual(diagnostic.details["record_index"], 0)

    def test_conversations_requires_mapping_object(self) -> None:
        for payload in (
            b'[{"id":"one"}]',
            b'[{"id":"one","mapping":[]}]',
            b'[{"id":"one","mapping":null}]',
        ):
            with self.subTest(payload=payload):
                result = self.validate("conversations.json", payload)
                self.assertFalse(result.is_valid)
                self.assertEqual(
                    result.diagnostics[0].code,
                    "CAE-M1-CONVERSATIONS-STRUCTURE-INVALID",
                )

    def test_conversations_requires_array_of_objects(self) -> None:
        wrong_root = self.validate("conversations.json", b"{}")
        self.assertEqual(wrong_root.diagnostics[0].code, "CAE-M1-JSON-TOP-LEVEL-TYPE")

        wrong_record = self.validate("conversations.json", b"[1]")
        self.assertEqual(
            wrong_record.diagnostics[0].code,
            "CAE-M1-CONVERSATIONS-STRUCTURE-INVALID",
        )

    def test_invalid_utf8_is_reported_without_content(self) -> None:
        result = self.validate("conversations.json", b"\xff\xfe")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.diagnostics[0].code, "CAE-M1-JSON-INVALID-UTF8")
        self.assertNotIn("\ufffd", result.diagnostics[0].message)

    def test_invalid_json_reports_line_and_column(self) -> None:
        result = self.validate("conversations.json", b"[\n{")
        self.assertFalse(result.is_valid)
        diagnostic = result.diagnostics[0]
        self.assertEqual(diagnostic.code, "CAE-M1-JSON-SYNTAX-ERROR")
        self.assertIn("line", diagnostic.details)
        self.assertIn("column", diagnostic.details)

    def test_json_null_is_wrong_top_level_type(self) -> None:
        result = self.validate("conversations.json", b"null")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.top_level_type, "null")
