# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog and the project uses Semantic Versioning.

## [Unreleased]

### Added

- Added `inspect-export` for read-only structural inspection of export directories and ZIP files.
- Added deterministic source inventory with required and known-file reporting.
- Added path traversal, symbolic-link, duplicate-path, and inventory-limit protections.
- Added stable M1 Slice 1 diagnostics and JSON output.

### Fixed

- Added `pytest` to the `dev` optional dependency set.
- Updated deprecated typing imports to their `collections.abc` locations.

## [0.1.0] - 2026-08-01

### Added

- Runnable CLI with `doctor`, `--help`, and `--version`.
- Platform-aware configuration and application data directory creation.
- Structured diagnostics and JSON-capable logging.
- Atomic filesystem write helper.
- Base exception hierarchy and stable exit codes.
- Primary application port contracts.
- Unit, integration, smoke, and packaging-oriented CI checks.
