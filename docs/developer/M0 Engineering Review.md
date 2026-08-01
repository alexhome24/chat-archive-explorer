# Milestone M0 Engineering Review

**Project:** Chat Archive Explorer  
**Milestone:** M0  
**Review status:** Passed  
**Review date:** 1 August 2026  
**Final revision:** macOS verification and Ruff formatting corrections included

## Scope

This review covers the implemented M0 project skeleton only. It does not introduce M1 functionality.

Normative references:

- `Export Format Specification v1.0`;
- `Architecture Specification v1.0`;
- `Implementation Roadmap v1.0`;
- `Developer Guide / Project Conventions v1.0`.

## Findings resolved during the initial engineering review

1. `filesystem.py` contained a no-op `pass` in the writable-directory probe. It was replaced with an explicit flush operation.
2. `application.doctor` directly imported a filesystem implementation. The dependency was inverted through `RuntimeFilesystemPort`; `LocalFilesystem` is supplied by the CLI composition root.

## Findings resolved during final macOS verification

The following defects were reproduced from the local verification report and corrected without changing M0 scope:

1. `pytest` was absent from `[project.optional-dependencies].dev`. The dependency set now includes `pytest>=8.0`, so `python -m pip install -e ".[dev]"` requests the complete M0 development toolchain: pytest, Ruff, mypy, and build.
2. Ruff rule `UP035` was triggered in `src/chat_archive_explorer/config.py`. `Mapping` is now imported from `collections.abc`.
3. Ruff rule `UP035` was triggered in `src/chat_archive_explorer/diagnostics/models.py`. `Mapping` is now imported from `collections.abc`; `Any` remains imported from `typing`.
4. The development-check examples in `README.md` now use the normative module-invocation commands, including `python -m pytest` and `python -m build`.
5. `.gitignore` was rechecked and contains `.venv/`, `dist/`, `build/`, and `*.egg-info/`.
6. A subsequent clean macOS check found that `python -m ruff format --check .` would reformat three files even though `python -m ruff check .` passed. Ruff formatting was applied to:
   - `src/chat_archive_explorer/filesystem.py`;
   - `tests/integration/test_cli.py`;
   - `tests/test_architecture.py`.

These corrections are maintenance fixes only. They do not add product functionality or alter the approved architecture or Roadmap.

## Verification results

### User-provided clean macOS verification

The final corrections were based on a clean macOS virtual-environment run that established:

| Check | Result |
|---|---|
| `python -m pip install -e .` | Passed; installed `chat-archive-explorer-0.1.0` |
| `chat-archive-explorer --version` | Passed; version `0.1.0` |
| `chat-archive-explorer doctor --json` | Passed; `healthy: true` |
| Test suite after adding pytest | 14 passed |
| Ruff findings before correction | Two `UP035` findings, both corrected |
| `python -m ruff check .` before final formatting correction | Passed: `All checks passed!` |
| `python -m ruff format --check .` before final formatting correction | Failed: three files required formatting |

### Final source-tree verification in the build environment

| Check | Result |
|---|---|
| `TODO` in production code | None |
| `FIXME` in production code | None |
| `pass` statements in production code | None |
| `NotImplementedError` in production code | None |
| Circular project imports | None across production modules |
| Domain outward dependencies | None |
| Application → infrastructure/presentation dependencies | None |
| CLI composition boundary | Compliant |
| Public package API | Limited to documented package version and architecture ports |
| Import-time filesystem/database/network side effects | None |
| Network-dependent runtime behavior | None |
| `python -m pytest` | 14 passed |
| Python compilation | Passed |
| Wheel build | Passed |
| Source distribution build | Passed |
| `chat-archive-explorer --version` | `chat-archive-explorer 0.1.0` |
| `chat-archive-explorer doctor --json` | Passed; `healthy: true` |

The isolated build environment could not obtain Ruff, mypy, or `build` from its configured package registry. Therefore those exact module commands were not re-executed there. The two reported Ruff lint violations and the three reported Ruff formatting differences were corrected directly. The clean macOS environment and repository CI remain the authoritative automated gates for Ruff, mypy, pytest, and `python -m build` on supported Python versions.

## Public API review

The package root exports only `__version__`. The application package exports the minimal M0 architecture contracts:

- `ImportSourcePort`;
- `BlobStorePort`;
- `RuntimeFilesystemPort`;
- `DiagnosticSink`;
- `SourceEntry`.

No adapter-specific JSON structures, filesystem implementation types, SQLite details, or future product APIs are exposed from the package root.

## Specification conformance

### Export Format Specification v1.0

M0 contains no export parsing behavior and introduces no conflicting interpretation of the ChatGPT export format.

### Architecture Specification v1.0

The dependency direction remains compliant:

- presentation/CLI performs composition;
- application services depend on ports rather than filesystem adapters;
- domain remains independent;
- infrastructure implements local runtime operations;
- diagnostics remain transport- and persistence-neutral.

### Implementation Roadmap v1.0

The M0 vertical slice remains exactly:

```text
CLI launch
  → doctor command
  → configuration validation
  → writable application directories
  → structured diagnostics
  → stable exit code
```

No M1 import, normalization, persistence, search, attachment, viewer, or exporter functionality has been added.

### Developer Guide / Project Conventions v1.0

Repository layout, naming, typing, logging, diagnostics, exception hierarchy, atomic writes, tests, packaging, CI configuration, optional development dependencies, and ignore rules conform to the guide.

## Final disposition

There are **no known unresolved deviations** from the four approved specifications within M0 scope.

The final Ruff formatting defect reported by local macOS verification has been resolved. No M1 functionality was introduced.

**Milestone M0 is fully closed and remains at version 0.1.0. M1 has not started.**
