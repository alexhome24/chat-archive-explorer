"""Minimal UTF-8, JSON, and top-level structure validation."""

from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import Any, BinaryIO

from chat_archive_explorer.application.import_models import LogicalFileValidation
from chat_archive_explorer.diagnostics import Diagnostic, DiagnosticSeverity


class OpenAIJsonValidator:
    """Validate required JSON files without normalizing source records."""

    def validate(self, path: PurePosixPath, stream: BinaryIO) -> LogicalFileValidation:
        """Validate one supported required logical file."""

        name = path.as_posix()
        try:
            raw = stream.read()
        except OSError as exc:
            return self._failure(
                name,
                "CAE-M1-JSON-OPEN-FAILED",
                "Required JSON file could not be read.",
                "Check source permissions or ZIP integrity and retry.",
                details={"error_type": type(exc).__name__},
            )

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            return self._failure(
                name,
                "CAE-M1-JSON-INVALID-UTF8",
                "Required JSON file is not valid UTF-8.",
                "Use an unmodified ChatGPT export and retry.",
                details={"start": exc.start, "end": exc.end},
            )

        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            return self._failure(
                name,
                "CAE-M1-JSON-SYNTAX-ERROR",
                "Required JSON file contains invalid JSON syntax.",
                "Use an intact export file and retry.",
                utf8_valid=True,
                details={"line": exc.lineno, "column": exc.colno, "position": exc.pos},
            )

        if name == "export_manifest.json":
            return self._validate_manifest(name, value)
        if name == "conversations.json":
            return self._validate_conversations(name, value)
        return self._failure(
            name,
            "CAE-M1-JSON-TOP-LEVEL-TYPE",
            "No minimal structure validator is registered for this logical file.",
            "Inspect only required files supported by this application version.",
            utf8_valid=True,
            json_valid=True,
            top_level_type=_json_type_name(value),
        )

    def _validate_manifest(self, name: str, value: Any) -> LogicalFileValidation:
        if not isinstance(value, dict):
            return self._top_level_failure(name, value, "object")
        export_files = value.get("export_files")
        if not isinstance(export_files, list):
            return self._structure_failure(
                name,
                "CAE-M1-MANIFEST-STRUCTURE-INVALID",
                "export_manifest.json must contain an export_files array.",
                {"field": "export_files"},
                top_level_type="object",
            )
        for index, entry in enumerate(export_files):
            if not isinstance(entry, dict):
                return self._structure_failure(
                    name,
                    "CAE-M1-MANIFEST-STRUCTURE-INVALID",
                    "Each export_files entry must be a JSON object.",
                    {"field": "export_files", "record_index": index},
                    top_level_type="object",
                    item_count=len(export_files),
                )
        return self._success(name, "object", len(export_files))

    def _validate_conversations(self, name: str, value: Any) -> LogicalFileValidation:
        if not isinstance(value, list):
            return self._top_level_failure(name, value, "array")
        for index, record in enumerate(value):
            if not isinstance(record, dict):
                return self._structure_failure(
                    name,
                    "CAE-M1-CONVERSATIONS-STRUCTURE-INVALID",
                    "Each conversation record must be a JSON object.",
                    {"record_index": index},
                    top_level_type="array",
                    item_count=len(value),
                )
            if "id" not in record and "conversation_id" not in record:
                return self._structure_failure(
                    name,
                    "CAE-M1-CONVERSATIONS-STRUCTURE-INVALID",
                    "Conversation record must contain id or conversation_id.",
                    {"record_index": index, "required_any": ["id", "conversation_id"]},
                    top_level_type="array",
                    item_count=len(value),
                )
            if not isinstance(record.get("mapping"), dict):
                return self._structure_failure(
                    name,
                    "CAE-M1-CONVERSATIONS-STRUCTURE-INVALID",
                    "Conversation record must contain mapping as a JSON object.",
                    {"record_index": index, "field": "mapping"},
                    top_level_type="array",
                    item_count=len(value),
                )
        return self._success(name, "array", len(value))

    def _success(self, name: str, top_level_type: str, item_count: int) -> LogicalFileValidation:
        diagnostic = Diagnostic(
            severity=DiagnosticSeverity.INFO,
            code="CAE-M1-JSON-VALID",
            message=f"Required JSON file passed minimal validation: {name}",
            source=name,
            details={"top_level_type": top_level_type, "item_count": item_count},
        )
        return LogicalFileValidation(
            path=name,
            utf8_valid=True,
            json_valid=True,
            top_level_type=top_level_type,
            structure_valid=True,
            item_count=item_count,
            diagnostics=(diagnostic,),
        )

    def _top_level_failure(self, name: str, value: Any, expected: str) -> LogicalFileValidation:
        actual = _json_type_name(value)
        return self._failure(
            name,
            "CAE-M1-JSON-TOP-LEVEL-TYPE",
            f"Required JSON file must have top-level type {expected}, not {actual}.",
            "Use an unmodified ChatGPT export and retry.",
            utf8_valid=True,
            json_valid=True,
            top_level_type=actual,
            details={"expected": expected, "actual": actual},
        )

    def _structure_failure(
        self,
        name: str,
        code: str,
        message: str,
        details: dict[str, object],
        *,
        top_level_type: str,
        item_count: int | None = None,
    ) -> LogicalFileValidation:
        return self._failure(
            name,
            code,
            message,
            "Use a complete, unmodified ChatGPT export and retry.",
            utf8_valid=True,
            json_valid=True,
            top_level_type=top_level_type,
            item_count=item_count,
            details=details,
        )

    def _failure(
        self,
        name: str,
        code: str,
        message: str,
        recovery: str,
        *,
        utf8_valid: bool = False,
        json_valid: bool = False,
        top_level_type: str | None = None,
        item_count: int | None = None,
        details: dict[str, object] | None = None,
    ) -> LogicalFileValidation:
        diagnostic = Diagnostic(
            severity=DiagnosticSeverity.ERROR,
            code=code,
            message=message,
            recovery=recovery,
            source=name,
            entity_id=name,
            details=details or {},
        )
        return LogicalFileValidation(
            path=name,
            utf8_valid=utf8_valid,
            json_valid=json_valid,
            top_level_type=top_level_type,
            structure_valid=False,
            item_count=item_count,
            diagnostics=(diagnostic,),
        )


def _json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__
