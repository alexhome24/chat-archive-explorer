# M1 Slice 2 Engineering Review

## Status

Implementation complete; local owner acceptance is still required before the Slice is closed.

## Implemented scope

- Required JSON files are opened through the existing read-only `ImportSourcePort`.
- `conversations.json` and `export_manifest.json` are decoded as UTF-8.
- JSON syntax is checked with Python's standard `json` module.
- Top-level types are checked: array for conversations and object for the manifest.
- Minimal confirmed structure is checked without domain normalization.
- A conversation record is accepted when it contains `id` or `conversation_id`; `mapping` is required and must be an object.
- `export_manifest.json` requires an `export_files` array whose entries are objects.
- Human-readable and JSON CLI reports include per-file logical validation results.
- Stable diagnostics include recovery guidance and never include conversation content.

## Explicitly outside scope

- Streaming or incremental JSON parsing.
- Performance optimization or record-size limits.
- Export format/version detection.
- Domain entities, normalization, graph reconstruction, branches, attachments, library records, blobs, SQLite, or persistence.

## Existing behavior preserved

- `doctor`, version reporting, exit codes, source inventory, directory/ZIP safety checks, and M1 Slice 1 output fields remain available.
- No M0 or M1 Slice 1 public API was removed.

## Refactoring

`inspect_export()` was split into private inventory, required-file, and logical-file validation stages. This was required to preserve readable orchestration while adding Slice 2. Public behavior from previous accepted work was not changed, and existing tests remain regression gates.

## Architecture review

- Application code depends only on `LogicalJsonValidatorPort`, not the concrete OpenAI validator.
- The concrete JSON validator is composed in the CLI composition root.
- Source-specific validation remains under `importers/openai_export` and does not create domain entities.
- The domain layer was not changed.
- Directory and ZIP adapters remain infrastructure details.
- No ADR or specification update was required.

## Diagnostics added

- `CAE-M1-JSON-OPEN-FAILED`
- `CAE-M1-JSON-INVALID-UTF8`
- `CAE-M1-JSON-SYNTAX-ERROR`
- `CAE-M1-JSON-TOP-LEVEL-TYPE`
- `CAE-M1-MANIFEST-STRUCTURE-INVALID`
- `CAE-M1-CONVERSATIONS-STRUCTURE-INVALID`
- `CAE-M1-JSON-VALID`

## Verified in the implementation environment

- `python -m pytest`: 45 tests passed, including 8 subtests.
- Python compilation of `src` and `tests`: passed.
- `git diff --check`: passed in the transported working tree.
- CLI smoke tests for valid and invalid required JSON: passed.
- Production architecture tests, circular-import checks, and placeholder checks: passed as part of pytest.

## Not executable in the implementation environment

The sandbox does not provide Ruff, mypy, or build. Their behavior was not imitated manually and no claim is made that these checks passed here.

## Required local acceptance

Run in the permanent Git working copy:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build
chat-archive-explorer --version
chat-archive-explorer doctor --json
chat-archive-explorer inspect-export <valid-source> --json
chat-archive-explorer inspect-export <invalid-source> --json
```

Automatic `python -m ruff format .` may be applied before commit if formatting is the only remaining issue, according to `DEVELOPMENT_WORKFLOW.md`.

## Known limitations

- Required JSON files are currently loaded fully into memory using standard-library JSON parsing.
- This is an intentional Slice 2 constraint. Streaming will be considered only if later measurements demonstrate a concrete need.

## Conclusion

M1 Slice 2 conforms to the accepted scope and the existing Export Format Specification, Architecture Specification, Developer Guide, Implementation Roadmap, and Development Workflow. It must not be considered accepted until the owner completes local acceptance, commit, and publication. The next Slice has not started.
