# Developer Guide / Project Conventions v1.0

**Project:** Chat Archive Explorer  
**Status:** Normative  
**Version:** 1.0  
**Audience:** Contributors and maintainers  
**Purpose:** Define day-to-day engineering conventions for implementation.

---

## 1. Purpose and Scope

This document defines repository, coding, testing, database, documentation, Git, compatibility, and change-management conventions.

It does **not** redefine:

- the ChatGPT export format — see `Export Format Specification v1.0`;
- the system architecture — see `Architecture Specification v1.0`;
- implementation order and milestone scope — see `Implementation Roadmap v1.0`.

Normative keywords:

- **MUST** — mandatory;
- **MUST NOT** — prohibited;
- **SHOULD** — expected unless a documented reason exists;
- **SHOULD NOT** — discouraged unless a documented reason exists;
- **MAY** — optional.

When this guide conflicts with a higher-level specification, the higher-level specification wins.

---

## 2. Repository Layout

The repository MUST use the following top-level layout unless changed by an approved ADR:

```text
chat-archive-explorer/
├── pyproject.toml
├── README.md
├── LICENSE
├── CHANGELOG.md
├── src/
│   └── chat_archive_explorer/
│       ├── application/
│       ├── domain/
│       ├── importers/
│       ├── storage/
│       ├── blobs/
│       ├── search/
│       ├── exporters/
│       ├── presentation/
│       ├── diagnostics/
│       └── cli/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── golden/
│   ├── property/
│   ├── performance/
│   └── fixtures/
├── docs/
│   ├── specifications/
│   ├── adr/
│   └── developer/
├── scripts/
├── migrations/
└── .github/
    └── workflows/
```

Rules:

- Production Python code MUST live under `src/chat_archive_explorer/`.
- Tests MUST mirror the production package structure where practical.
- Test fixtures MUST NOT be stored inside production packages.
- Generated files, local databases, imported archives, caches, and build artifacts MUST NOT be committed.
- New top-level directories MUST require an ADR or an explicit architecture update.
- Cross-cutting helpers MUST NOT be placed in a generic `utils.py` unless their scope is truly project-wide and stable.
- Domain concepts MUST live in `domain/`, not in adapters or UI modules.
- OpenAI-specific parsing code MUST live under `importers/` and MUST NOT leak into the domain layer.

---

## 3. Naming Conventions

### 3.1 Python names

- Packages and modules MUST use `snake_case`.
- Classes and exceptions MUST use `PascalCase`.
- Functions, methods, variables, and parameters MUST use `snake_case`.
- Constants MUST use `UPPER_SNAKE_CASE`.
- Private implementation details SHOULD use a single leading underscore.
- Exception classes MUST end with `Error`.
- Protocols and abstract interfaces MUST use descriptive domain names and MUST NOT use Hungarian-style prefixes such as `IRepository`.
- Boolean names SHOULD begin with `is_`, `has_`, `can_`, `should_`, or `was_`.
- Collection names SHOULD be plural.

### 3.2 Files and directories

- Python files MUST use `.py` and `snake_case` names.
- Specification and policy documents SHOULD use title case with a version suffix.
- ADR files MUST use the format `NNNN-short-kebab-case-title.md`.
- Database migration files MUST use the format `NNNN_short_description.sql` or the migration tool's equivalent deterministic format.
- Test files MUST use `test_<subject>.py`.

### 3.3 Domain identifiers

- External IDs from an export MUST be preserved exactly as received.
- Internal IDs MUST be opaque to callers.
- Code MUST NOT infer semantic meaning from UUID shape, prefix, or length unless defined by a specification.
- Physical blob identity MUST be based on content hash where required by `Architecture Specification v1.0`.

---

## 4. Code Style

- Supported Python versions MUST be declared in `pyproject.toml`.
- All public functions, methods, classes, and module-level variables SHOULD have type annotations.
- New code MUST pass the configured formatter, linter, and type checker.
- Line length MUST be enforced by the project formatter; hand-wrapping SHOULD be avoided where the formatter can decide.
- `pathlib.Path` MUST be used for filesystem paths.
- File operations MUST specify binary or text mode explicitly.
- Text operations MUST specify encoding explicitly; UTF-8 SHOULD be the default.
- Domain records SHOULD use immutable data structures where practical.
- `dataclass` MAY be used for value objects and transport-neutral records.
- Global mutable state MUST NOT be used.
- Import-time side effects MUST NOT access files, databases, network resources, or environment-dependent state.
- Public APIs MUST NOT expose adapter-specific JSON dictionaries when a domain type exists.
- Functions SHOULD have one primary responsibility.
- A module SHOULD stay focused on one bounded responsibility.
- Circular imports MUST be treated as a design defect, not patched with runtime imports except as a temporary documented workaround.
- Broad `except Exception` blocks MUST NOT suppress failures.
- Production code MUST NOT use `print()` for diagnostics.

---

## 5. Documentation Rules

- `README.md` MUST explain installation, basic usage, supported platforms, project status, and links to normative specifications.
- Public extension points MUST be documented.
- User-visible behavior changes MUST update relevant documentation in the same change.
- Documentation MUST link to existing normative documents instead of duplicating their content.
- Examples MUST be executable or clearly marked as pseudocode.
- File paths, commands, identifiers, and code symbols MUST use inline code formatting.
- Normative documents MUST include a version and status.
- Outdated documentation MUST be corrected or removed in the same change that makes it outdated.

---

## 6. Logging

- The project MUST use Python's standard `logging` API or a compatible facade approved by ADR.
- Each module MUST use a named logger derived from `__name__`.
- Logs MUST describe events, not reproduce entire source records.
- Conversation content, attachment content, personal data, authentication data, and full raw metadata MUST NOT be logged by default.
- File paths SHOULD be minimized or redacted when they may reveal user information.
- Structured context SHOULD be supplied through logger fields rather than string concatenation where supported.
- Log levels MUST be used consistently:
  - `DEBUG`: developer diagnostics;
  - `INFO`: normal lifecycle milestones;
  - `WARNING`: recoverable anomaly or degraded behavior;
  - `ERROR`: failed operation requiring user or operator attention;
  - `CRITICAL`: process-level integrity or availability failure.
- Expected validation failures MUST NOT produce stack traces at `INFO` or `WARNING` level.
- Unexpected exceptions SHOULD include stack traces at `ERROR` level.
- Log messages SHOULD include stable event names or codes for machine filtering.

---

## 7. Error Handling

### 7.1 General rules

- Errors MUST be classified as domain, validation, storage, blob, import, export, search, configuration, or infrastructure failures.
- User-correctable failures MUST produce actionable diagnostics.
- Internal exceptions MUST NOT be exposed directly to end users.
- Exceptions MUST preserve their causal chain using `raise ... from ...` where appropriate.
- Errors MUST NOT be silently ignored.
- Partial-success operations MUST return or persist explicit diagnostics.
- Recoverable per-record failures SHOULD NOT abort an entire import unless integrity would be compromised.
- Integrity failures MUST abort the affected transaction or import stage.

### 7.2 Exception hierarchy

The project MUST maintain a small root hierarchy, for example:

```text
ChatArchiveError
├── ConfigurationError
├── ValidationError
├── ImportError
├── StorageError
├── BlobError
├── SearchError
└── ExportError
```

Exact classes MAY evolve without an architecture change if subsystem boundaries remain unchanged.

### 7.3 Diagnostics

- Machine-readable diagnostic codes MUST be stable once released.
- Each diagnostic SHOULD include severity, code, message, source location, related entity ID, and recovery guidance when available.
- Diagnostics MUST be storable independently from logs.
- Raw external values SHOULD be preserved when necessary to explain a failure, subject to privacy rules.

---

## 8. SQLite Conventions

- All SQL MUST use parameterized statements.
- Application code MUST NOT build SQL by interpolating user or export values.
- Foreign keys MUST be enabled for every connection.
- Schema initialization and migration MUST run before normal repository use.
- Write operations MUST use explicit transaction boundaries.
- A transaction MUST cover one consistency unit, not an arbitrary amount of work.
- Long-running file hashing or parsing MUST NOT occur while holding a write transaction.
- Bulk inserts SHOULD use batched transactions.
- Read-only operations SHOULD use read-only connections when practical.
- Repository code MUST own SQL; UI and domain code MUST NOT issue SQL directly.
- Database rows MUST be mapped to domain or repository records before leaving the storage layer.
- SQLite pragmas MUST be configured centrally.
- WAL mode SHOULD be used unless platform testing shows a concrete incompatibility.
- Migrations MUST be deterministic and idempotent at the migration-runner level.
- Application startup MUST refuse to operate on a database schema newer than the application supports.
- Database backups or recovery points SHOULD be created before destructive migrations.

---

## 9. Blob Storage Conventions

- Blob storage MUST follow `Architecture Specification v1.0`.
- Stored blobs MUST be immutable.
- Blob identity MUST be based on SHA-256 unless superseded by an approved architecture decision.
- Blob ingestion MUST verify the computed hash before committing metadata.
- A blob MUST be written atomically using a temporary path followed by rename or equivalent safe operation.
- Duplicate physical content SHOULD map to one stored blob and multiple logical references.
- Original external file names MUST be metadata, not storage paths.
- User-provided paths MUST NOT determine final blob locations.
- Blob paths MUST be platform-safe and deterministic.
- Deleting a logical attachment MUST NOT delete a shared blob while references remain.
- Blob garbage collection MUST be explicit, testable, and reference-aware.
- The application MUST distinguish missing blob, corrupt blob, and unlinked blob states.

---

## 10. Testing Strategy

### 10.1 General requirements

- Every bug fix MUST include a regression test unless technically impossible and documented.
- New behavior MUST include tests at the lowest effective level.
- Tests MUST be deterministic.
- Tests MUST NOT require internet access.
- Tests MUST NOT depend on a developer's home directory, locale, timezone, or existing application database.
- Temporary files and databases MUST use isolated test directories.
- Real user data MUST NOT be committed as fixtures.
- Fixtures derived from exports MUST be minimized and sanitized.

### 10.2 Unit tests

- Unit tests MUST isolate one component or rule.
- Unit tests SHOULD avoid SQLite and filesystem access unless those are the unit under test.
- Domain normalization, validation, branch handling, and conflict-resolution rules MUST have unit coverage.

### 10.3 Integration tests

- Integration tests MUST cover component boundaries such as importer-to-storage, storage-to-search, and blob-to-attachment linking.
- SQLite integration tests MUST use the real schema and migration path.
- Import integration tests SHOULD use complete minimal export fixtures.

### 10.4 Golden tests

- Golden tests MUST be used for deterministic HTML, Markdown, normalized JSON, and diagnostics outputs.
- Golden files MUST be human-reviewable.
- Golden updates MUST be explicit and reviewed as behavior changes.
- Golden tests MUST normalize unstable values such as timestamps, temporary paths, or generated IDs.

### 10.5 Property-based tests

- Property tests SHOULD cover graph invariants, ID preservation, normalization idempotence, and round-trip-safe serialization where applicable.
- Property tests MUST use bounded inputs suitable for CI.
- A failing generated case MUST be retained as a deterministic regression case.

### 10.6 Performance tests

- Performance tests MUST track import throughput, peak memory, search latency, and export time for agreed fixture sizes.
- Performance thresholds MUST be versioned in the Roadmap or release criteria, not hidden in ad hoc tests.
- Performance regressions above the accepted threshold MUST block release unless explicitly waived.

---

## 11. Comments and Docstrings

- Comments MUST explain intent, constraints, or non-obvious trade-offs.
- Comments MUST NOT restate code.
- Workarounds MUST include the reason and a removal condition.
- `TODO` comments MUST include an issue reference or a concrete completion condition.
- Public modules, classes, protocols, functions, and methods SHOULD have concise docstrings.
- Docstrings MUST describe contract, important invariants, raised exceptions, and side effects when relevant.
- Internal trivial functions MAY omit docstrings when names and types are sufficient.
- Docstrings MUST NOT duplicate type annotations.
- Architecture rationale MUST live in specifications or ADRs, not large code comments.

---

## 12. Architecture Decision Records

- ADRs MUST be stored under `docs/adr/`.
- ADR numbering MUST be sequential and never reused.
- An ADR MUST use the following sections:
  - Title;
  - Status;
  - Context;
  - Decision;
  - Consequences;
  - Alternatives considered;
  - References.
- Allowed statuses: `Proposed`, `Accepted`, `Superseded`, `Deprecated`, `Rejected`.
- Accepted ADRs MUST NOT be edited to change the original decision; a new ADR MUST supersede them.
- Minor corrections MAY be made if they do not alter meaning.
- An ADR MUST be created when a decision changes component boundaries, durable storage format, public extension contracts, security model, or cross-cutting technology policy.
- An ADR MAY document a significant implementation choice that does not require a specification revision.
- ADRs MUST reference affected specifications and issues.

---

## 13. Git Workflow

- `main` MUST remain releasable.
- Work MUST occur in short-lived branches.
- Branch names SHOULD use:
  - `feature/<short-name>`;
  - `fix/<short-name>`;
  - `docs/<short-name>`;
  - `refactor/<short-name>`;
  - `chore/<short-name>`.
- Direct pushes to protected `main` MUST NOT be allowed.
- Changes MUST be integrated through pull requests.
- Pull requests MUST be focused and reviewable.
- Pull requests MUST include purpose, scope, tests, user-visible impact, and specification or ADR impact.
- Required CI checks MUST pass before merge.
- At least one review SHOULD be required for non-trivial changes.
- Squash merge SHOULD be the default unless preserving a curated commit series adds value.
- Force-pushing shared long-lived branches MUST NOT be allowed.
- Release tags MUST be signed when project infrastructure supports it.

---

## 14. Commit Messages

The project MUST use Conventional Commits.

Allowed common types:

```text
feat
fix
docs
test
refactor
perf
build
ci
chore
revert
```

Format:

```text
<type>(optional-scope): <imperative summary>
```

Examples:

```text
feat(import): add manifest validation stage
fix(graph): preserve alternative branch ordering
test(storage): cover rollback on blob failure
docs(adr): record SQLite migration policy
```

Rules:

- The summary MUST use imperative mood.
- The summary MUST NOT end with a period.
- Breaking changes MUST use `!` or a `BREAKING CHANGE:` footer.
- Commits SHOULD be logically atomic.
- Generated artifacts MUST NOT be mixed with unrelated source changes.

---

## 15. Versioning and Compatibility

- Application releases MUST follow Semantic Versioning.
- Pre-1.0 releases MAY introduce breaking changes only when documented in the changelog and migration notes.
- Public CLI behavior, persisted database schema, normalized export schema, plugin contracts, and documented extension APIs are compatibility surfaces.
- Internal modules are not public APIs unless explicitly documented.
- Deprecations SHOULD remain for at least one minor release after 1.0.
- Deprecated behavior MUST emit a clear warning where practical.
- Breaking changes MUST update `CHANGELOG.md` and relevant migration guidance.
- Export adapters MUST declare the external format variants they support.
- Compatibility guarantees MUST NOT exceed what is stated in normative specifications.

---

## 16. Database Schema Changes and Migrations

- Every persistent schema change MUST include a migration.
- Schema changes MUST NOT be performed ad hoc at runtime outside the migration system.
- Migration numbering MUST be monotonic.
- Applied migrations MUST be recorded in the database.
- Migrations MUST be tested from:
  - a fresh database;
  - the immediately previous supported schema;
  - the oldest schema supported by the release, when applicable.
- Destructive migrations MUST preserve recoverability through backup, copy-on-write, or explicit export guidance.
- Data backfills MUST be restartable or transactionally safe.
- A migration MUST NOT depend on network access.
- Database schema version and application compatibility MUST be checked at startup.
- A schema change that alters domain persistence semantics requires an ADR and MAY require an architecture specification update.

---

## 17. Export Adapter Policy

- OpenAI export-specific logic MUST remain inside export adapter modules.
- Adapters MUST produce normalized application contracts defined by `Architecture Specification v1.0`.
- Adapters MUST preserve unknown fields in the raw preservation mechanism defined by the architecture.
- New external fields MUST NOT be added directly to the domain model without a demonstrated domain need.
- New roles, content types, metadata variants, or link forms MUST initially be handled as extensible values, not closed enumerations that reject imports.
- An adapter MUST validate required structural relationships before normalization.
- An adapter MUST emit diagnostics for unsupported or conflicting external data.
- Adapter behavior MUST be covered by version-specific fixtures and regression tests.
- Support for a new OpenAI export variant SHOULD be implemented as:
  1. detection;
  2. version-specific parsing;
  3. normalization;
  4. compatibility tests;
  5. documentation update.
- A new adapter version MUST NOT require domain changes unless the new source concept cannot be represented without data loss.
- If domain changes are required, the change MUST follow the architectural change policy.

---

## 18. Backward Compatibility

- Existing imported libraries MUST remain readable across compatible releases.
- Database migration MUST preserve normalized user data unless a breaking release explicitly states otherwise.
- Previously generated exports SHOULD remain reproducible within documented formatting tolerances.
- Existing command-line options MUST NOT silently change meaning.
- Diagnostic codes MUST remain stable once published.
- Unknown preserved source data MUST survive re-indexing, migration, and re-export where the relevant exporter supports raw preservation.
- Removal of a supported export adapter, database version, CLI option, or public extension point requires deprecation or a major-version change after 1.0.

---

## 19. Security and Privacy

- Core application functionality MUST work without network access.
- Telemetry MUST NOT be introduced without an explicit architecture decision and opt-in design.
- Conversation and attachment contents MUST NOT be logged by default.
- Import paths and archive entries MUST be treated as untrusted input.
- Archive extraction MUST prevent path traversal, absolute-path writes, and symlink escape.
- Exported file names MUST be sanitized before filesystem use.
- SQL, HTML, Markdown, and shell contexts MUST use context-appropriate escaping.
- Blob and export writes MUST use safe temporary paths and atomic replacement where possible.
- Secrets and personal data MUST NOT be committed to fixtures, logs, screenshots, or issue templates.
- Security-sensitive fixes SHOULD include regression tests.

---

## 20. Performance Guidelines

- Large files MUST be processed in streaming mode where practical.
- Import code MUST avoid loading all blob contents into memory.
- SHA-256 MUST be computed incrementally.
- Database writes SHOULD be batched.
- Search indexing SHOULD support incremental updates.
- UI and presentation layers MUST NOT block on long-running import, hashing, or indexing work.
- N+1 database query patterns SHOULD be avoided.
- Performance optimization MUST be based on measurement.
- Complexity-sensitive code SHOULD document expected asymptotic behavior when non-obvious.
- Caches MUST have explicit ownership, invalidation, and size policies.

---

## 21. Architectural Change Policy

A change is architectural when it modifies one or more of the following:

- domain model semantics;
- component or layer boundaries;
- dependency direction;
- importer pipeline stages or contracts;
- durable database or blob-storage model;
- public extension interfaces;
- normalized internal data contracts;
- security or privacy model;
- branch or graph representation;
- source-of-truth rules between competing data sources.

Architectural changes:

- MUST include an ADR;
- MUST update `Architecture Specification v1.0` or create its successor;
- MUST assess effects on the Roadmap, migrations, compatibility, tests, and documentation.

The following normally do not require architecture changes:

- internal refactoring that preserves contracts;
- adding tests;
- local performance improvements;
- adding a new exporter behind an existing exporter contract;
- adding support for a new external export variant through the existing adapter contract;
- UI styling changes;
- bug fixes that restore specified behavior.

When uncertain, contributors MUST open an issue or proposed ADR before implementation.

---

## 22. Specification Governance

Normative precedence:

1. `Export Format Specification v1.0` — external format facts and validated source-of-truth rules;
2. `Architecture Specification v1.0` — system structure and contracts;
3. `Developer Guide / Project Conventions v1.0` — engineering practice;
4. `Implementation Roadmap v1.0` — delivery sequence and milestone scope.

Rules:

- A lower-precedence document MUST NOT override a higher-precedence document.
- Changes to normative documents MUST occur in the same pull request as the change that requires them.
- Specification versions MUST be explicit.
- Superseded specifications MUST remain in version control and be marked as superseded.
- New project-wide documents SHOULD NOT be created when an existing specification, ADR, issue, or code-level document is sufficient.
- New design documents MUST be justified by a real unresolved decision.
- Once implementation begins, documentation effort SHOULD prioritize correctness, operability, and contributor onboarding over speculative design.

---

## 23. First-Time Contributor Checklist

Before starting work, a contributor MUST:

1. read `README.md`;
2. identify the relevant milestone in `Implementation Roadmap v1.0`;
3. read the affected sections of `Architecture Specification v1.0`;
4. read export-format rules only when changing importer or compatibility behavior;
5. check existing ADRs;
6. create or link an issue for non-trivial work;
7. add or update tests with the change;
8. verify whether the change is architectural under Section 21.

Before opening a pull request, a contributor MUST:

1. run formatting, linting, type checking, and relevant tests;
2. confirm no private archive data or generated local artifacts are included;
3. update documentation and migrations when required;
4. state whether specifications or ADRs are affected;
5. provide reproducible validation steps.

---

## 24. Completion Status

With approval of this document, the preparation phase is complete.

Further design documents SHOULD NOT be created unless implementation exposes a decision not covered by:

- `Export Format Specification v1.0`;
- `Architecture Specification v1.0`;
- `Implementation Roadmap v1.0`;
- this guide;
- an existing ADR.

Implementation MAY proceed with Milestone M0.
