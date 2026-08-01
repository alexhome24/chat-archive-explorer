from __future__ import annotations

import json
import unittest

from chat_archive_explorer.diagnostics import Diagnostic, DiagnosticSeverity


class DiagnosticTests(unittest.TestCase):
    def test_serialization_uses_stable_machine_readable_fields(self) -> None:
        diagnostic = Diagnostic(
            severity=DiagnosticSeverity.WARNING,
            code="CAE-TEST-001",
            message="Example warning.",
            recovery="Retry with a writable directory.",
            details={"attempt": 1},
        )
        encoded = json.dumps(diagnostic.to_dict(), sort_keys=True)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["severity"], "warning")
        self.assertEqual(decoded["code"], "CAE-TEST-001")
        self.assertEqual(decoded["details"], {"attempt": 1})
