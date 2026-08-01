"""Stable, serializable diagnostic records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DiagnosticSeverity(StrEnum):
    """Diagnostic severity ordered by operational impact."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """Machine-readable result that can be stored independently from logs."""

    severity: DiagnosticSeverity
    code: str
    message: str
    recovery: str | None = None
    source: str | None = None
    entity_id: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize using stable field names suitable for JSON output."""

        payload: dict[str, Any] = {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
        }
        if self.recovery is not None:
            payload["recovery"] = self.recovery
        if self.source is not None:
            payload["source"] = self.source
        if self.entity_id is not None:
            payload["entity_id"] = self.entity_id
        if self.details:
            payload["details"] = dict(self.details)
        return payload
