"""Command-line entry point for Chat Archive Explorer."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from chat_archive_explorer.application.doctor import DoctorReport, run_doctor
from chat_archive_explorer.application.import_inspection import inspect_export
from chat_archive_explorer.application.import_models import ExportInspectionReport
from chat_archive_explorer.config import AppConfig
from chat_archive_explorer.errors import ChatArchiveError, ExitCode
from chat_archive_explorer.filesystem import LocalFilesystem
from chat_archive_explorer.infrastructure.import_sources import LocalImportSourceFactory
from chat_archive_explorer.logging_config import configure_logging
from chat_archive_explorer.version import __version__

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser."""

    parser = argparse.ArgumentParser(
        prog="chat-archive-explorer",
        description="Local, offline explorer for ChatGPT data exports.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--debug", action="store_true", help="enable developer debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="verify configuration and local directories")
    doctor.add_argument("--json", action="store_true", help="write machine-readable JSON")

    inspect_command = subparsers.add_parser(
        "inspect-export", help="inspect the structure of an export directory or ZIP"
    )
    inspect_command.add_argument("source", type=Path, help="export directory or ZIP path")
    inspect_command.add_argument("--json", action="store_true", help="write machine-readable JSON")
    return parser


def _print_human_report(report: DoctorReport) -> None:
    print(f"Chat Archive Explorer {report.application_version}")
    print(f"Schema version: {report.schema_version}")
    print(f"Data directory: {report.data_dir}")
    print(f"Status: {'healthy' if report.is_healthy else 'unhealthy'}")
    for diagnostic in report.diagnostics:
        print(f"[{diagnostic.severity.value}] {diagnostic.code}: {diagnostic.message}")


def _print_inspection_report(report: ExportInspectionReport) -> None:
    print(f"Source: {report.source}")
    print(f"Source kind: {report.source_kind or 'unavailable'}")
    if report.inventory is not None:
        print(f"Entries: {report.inventory.entry_count}")
        print(f"Total size: {report.inventory.total_size} bytes")
    print(f"Status: {'valid' if report.is_valid else 'invalid'}")
    if report.required_files_present:
        print("Required files present: " + ", ".join(report.required_files_present))
    if report.required_files_missing:
        print("Required files missing: " + ", ".join(report.required_files_missing))
    if report.known_files_present:
        print("Known optional files: " + ", ".join(report.known_files_present))
    for diagnostic in report.diagnostics:
        print(f"[{diagnostic.severity.value}] {diagnostic.code}: {diagnostic.message}")
        if diagnostic.recovery is not None:
            print(f"  Recovery: {diagnostic.recovery}")


def run(argv: Sequence[str] | None = None) -> int:
    """Execute one CLI command and return a stable process exit code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = AppConfig.from_environment()
        configure_logging(level=config.log_level, output_format=config.log_format, debug=args.debug)

        if args.command == "doctor":
            report = run_doctor(config, LocalFilesystem())
            if args.json:
                print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
            else:
                _print_human_report(report)
            return int(ExitCode.SUCCESS if report.is_healthy else ExitCode.VALIDATION_ERROR)

        if args.command == "inspect-export":
            inspection = inspect_export(args.source, LocalImportSourceFactory())
            if args.json:
                print(
                    json.dumps(inspection.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
                )
            else:
                _print_inspection_report(inspection)
            return int(ExitCode.SUCCESS if inspection.is_valid else ExitCode.VALIDATION_ERROR)

        parser.error(f"Unsupported command: {args.command}")
        return int(ExitCode.USAGE)
    except ChatArchiveError as exc:
        logger.error("expected application failure", extra={"event": "CAE-CLI-EXPECTED-ERROR"})
        print(f"Error: {exc}", file=sys.stderr)
        return int(exc.exit_code)
    except Exception:
        logger.exception(
            "unexpected application failure",
            extra={"event": "CAE-CLI-INTERNAL-ERROR"},
        )
        print("Error: unexpected internal failure", file=sys.stderr)
        return int(ExitCode.INTERNAL_ERROR)


def main() -> None:
    """Console-script wrapper."""

    raise SystemExit(run())
