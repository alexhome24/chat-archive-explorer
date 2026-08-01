# M1 Slice 1 Engineering Review

## Status

**Implementation complete; awaiting maintainer acceptance and macOS verification.**

This review covers only M1 Slice 1: read-only source acquisition, physical inventory, and root-level structural checks for a directory or ZIP. It does not declare Milestone M1 complete.

## Implemented functionality

- Added `chat-archive-explorer inspect-export <source>` with human-readable output.
- Added `chat-archive-explorer inspect-export <source> --json` with stable machine-readable output.
- Added read-only directory and ZIP implementations of `ImportSourcePort`.
- Added a composition-root factory for selecting directory or ZIP adapters.
- Added deterministic inventory entries containing normalized POSIX path, uncompressed size, and ZIP compressed size when available.
- Added metadata-derived source fingerprints without reading entry contents.
- Added root-level checks for:
  - `conversations.json`;
  - `export_manifest.json`.
- Added reporting of known optional export files without parsing them.
- Added protections against:
  - absolute and traversal paths;
  - symbolic links;
  - duplicate normalized paths;
  - excessive entry counts;
  - excessive total uncompressed size;
  - invalid or unsupported source files.
- Added actionable structured diagnostics and stable exit code `20` for failed structural inspection.
- Preserved all M0 commands and behavior, including version `0.1.0` and `doctor`.

## Intentionally outside scope

The slice does not:

- parse or validate JSON syntax;
- inspect JSON shapes or values;
- identify an export format family or version;
- read or validate the export manifest;
- normalize conversations, nodes, messages, content, branches, or attachments;
- inspect `.dat` payloads;
- extract ZIP files;
- write SQLite or blob storage;
- persist an import;
- search or export conversations.

Passing `inspect-export` therefore means only that the selected source was opened safely, inventoried, and contains the two required root-level files.

## Public API changes

Added or extended:

- `ImportSourceFactoryPort`;
- `ImportSourcePort.source_kind`;
- `SourceEntry.compressed_size`;
- `inspect_export()`;
- `InventoryEntry`;
- `SourceInventory`;
- `ExportInspectionReport`;
- `DirectoryImportSource`;
- `ZipImportSource`;
- `LocalImportSourceFactory`;
- CLI command `inspect-export`.

No existing public function, command, exit code, or M0 behavior was removed or changed.

## Diagnostic codes

- `CAE-M1-SOURCE-OPENED`
- `CAE-M1-SOURCE-NOT-FOUND`
- `CAE-M1-SOURCE-NOT-READABLE`
- `CAE-M1-SOURCE-UNSUPPORTED`
- `CAE-M1-ZIP-INVALID`
- `CAE-M1-ENTRY-UNSAFE-PATH`
- `CAE-M1-ENTRY-DUPLICATE-PATH`
- `CAE-M1-SOURCE-LIMIT-EXCEEDED`
- `CAE-M1-INVENTORY-COMPLETE`
- `CAE-M1-REQUIRED-FILE-MISSING`
- `CAE-M1-SOURCE-STRUCTURE-VALID`

Error diagnostics include source information and recovery guidance. No diagnostic claims that an OpenAI format profile or version was detected.

## Refactoring performed during this slice

No behavioral refactoring of M0 was required.

The existing architecture contracts were extended minimally with source-kind metadata, ZIP compressed size, and a factory port. The existing exception hierarchy was extended with `ImportSourceError` so expected acquisition failures can be converted to structured diagnostics. These changes do not alter M0 behavior or its public commands.

## Test coverage added

### Unit

- deterministic structural inspection and serialization;
- independent reporting of missing required files;
- recursive directory inventory and binary stream opening;
- directory symbolic-link rejection;
- ZIP inventory and stream opening without extraction;
- ZIP traversal rejection;
- duplicate normalized ZIP path rejection;
- source factory selection;
- missing source, plain file, and invalid ZIP diagnostics.

### Integration

- equivalent successful directory and ZIP structural checks;
- machine-readable JSON output;
- missing required file with exit code `20` and no traceback;
- missing source with structured JSON diagnostic;
- invalid JSON marker contents still pass Slice 1, proving JSON is not parsed;
- M0 `doctor` and configuration-error behavior remain unchanged.

### Architecture

- application layer remains independent of infrastructure and presentation;
- infrastructure does not import CLI or presentation;
- no circular project imports;
- no `TODO`, `FIXME`, `NotImplementedError`, or `pass` statements in production code.

## Final macOS formatting correction

The maintainer's clean macOS verification found one remaining formatting-only discrepancy after the initial slice archive was produced:

- `python -m pytest`: **29 passed**;
- `python -m ruff check .`: **All checks passed**;
- `python -m ruff format --check .`: reported two files requiring formatting.

Only the following files were reformatted, with no functional or scope changes:

- `src/chat_archive_explorer/cli/main.py`;
- `src/chat_archive_explorer/infrastructure/import_sources/directory.py`.

The sandbox test suite was rerun after this correction and again reported **29 passed**. Ruff is not executable in this Linux sandbox, so the final `ruff check` and `ruff format --check` commands remain a maintainer-side acceptance gate for this corrected archive.

## Checks executed in the sandbox

| Check | Result |
|---|---|
| `PYTHONPATH=src python -m pytest` | **29 passed** |
| `PYTHONPATH=src python -m compileall -q src tests` | Passed |
| `PYTHONPATH=src python -m chat_archive_explorer --version` | `chat-archive-explorer 0.1.0` |
| Directory `inspect-export --json` smoke test | Valid, exit `0` |
| ZIP `inspect-export --json` smoke test | Valid, exit `0` |
| Missing source smoke test | Invalid, exit `20` |
| `git diff --check` | Passed |
| Wheel build through PEP 517 backend | Passed |
| sdist build through setuptools backend | Passed |

The exact commands `python -m ruff`, `python -m mypy`, and `python -m build` could not be executed in this Linux sandbox. The uploaded working tree contained macOS ARM64 development binaries, which are not executable here, and the sandbox package index did not provide replacement packages. The maintainer must run the standard project checks in the real macOS environment before commit.

The build backend itself was exercised successfully: a wheel and sdist were produced. Setuptools emitted pre-existing license-metadata deprecation warnings; changing packaging metadata is outside this slice.

## Architecture review

### Export Format Specification v1.0

Conforms. The slice checks only confirmed logical filenames and does not infer format version, parse content, reinterpret `.dat`, or treat optional files as mandatory.

### Architecture Specification v1.0

Conforms.

- Acquisition is read-only.
- ZIP entries are streamed and never extracted.
- Inventory is distinct from future manifest validation.
- Application logic depends on ports, not concrete filesystem or ZIP adapters.
- Concrete adapters are composed in the CLI layer.
- Archive path and size limits are enforced before content parsing.

### Developer Guide / Project Conventions v1.0

Conforms based on available checks.

- New behavior is covered at unit and integration levels.
- Expected failures produce actionable diagnostics.
- No conversation content or raw records are logged.
- Module responsibilities remain focused.
- No temporary implementation or duplicated acquisition logic was introduced.

Ruff and mypy remain mandatory maintainer-side gates because they were unavailable in the sandbox.

### Implementation Roadmap v1.0

Conforms to the approved reduced scope of M1 Slice 1: acquisition, inventory, and root-level structural checks only. Later M1 work remains necessary for JSON validation, format detection, parsing, graph validation, and normalization.

## Known limitations

These are intentional Slice 1 boundaries, not unresolved defects:

- Required files must be located at the selected source root; a wrapping directory inside a ZIP is not auto-unwrapped.
- Fingerprints identify an inventory snapshot from normalized paths and sizes; they are not content hashes.
- JSON files may be malformed and still pass this structural slice.
- ZIP encryption and entry-content readability are not tested until a later stage opens logical files.
- Inventory safety limits are fixed at 250,000 entries and 100 GiB total uncompressed size.
- The command does not claim export-format or version detection.

## Files changed

### Existing files modified

- `CHANGELOG.md`
- `README.md`
- `src/chat_archive_explorer/application/__init__.py`
- `src/chat_archive_explorer/application/ports.py`
- `src/chat_archive_explorer/cli/main.py`
- `src/chat_archive_explorer/errors.py`
- `tests/integration/test_cli.py`
- `tests/test_architecture.py`

### New production files

- `src/chat_archive_explorer/application/import_inspection.py`
- `src/chat_archive_explorer/application/import_models.py`
- `src/chat_archive_explorer/infrastructure/__init__.py`
- `src/chat_archive_explorer/infrastructure/import_sources/__init__.py`
- `src/chat_archive_explorer/infrastructure/import_sources/common.py`
- `src/chat_archive_explorer/infrastructure/import_sources/directory.py`
- `src/chat_archive_explorer/infrastructure/import_sources/factory.py`
- `src/chat_archive_explorer/infrastructure/import_sources/zip.py`

### New tests

- `tests/unit/test_directory_import_source.py`
- `tests/unit/test_import_inspection.py`
- `tests/unit/test_import_source_factory.py`
- `tests/unit/test_zip_import_source.py`

### New engineering report

- `docs/developer/M1 Slice 1 Engineering Review.md`

## Review conclusion

No architecture contradiction, ADR requirement, deliberate technical debt, temporary code, or unresolved specification deviation was identified.

M1 Slice 1 is ready for maintainer-side macOS checks and acceptance. Work on the next M1 slice must not begin until this slice is accepted.
