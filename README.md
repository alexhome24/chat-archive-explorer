# Chat Archive Explorer

Local, offline tooling for turning a ChatGPT export into a durable, searchable archive.

## Project status

Milestone **M0** and the first vertical slice of **M1** are implemented. The repository provides
a runnable CLI, configuration, structured diagnostics and logging, filesystem self-checks, safe
read-only directory/ZIP source adapters, structural export inventory, and minimal validation of the
required JSON files. It does **not** normalize conversations, build message graphs, or persist
imported data yet.

## Requirements

- Python 3.11 or newer
- macOS is the primary development platform; the core is kept portable to Windows and Linux
- No network connection is required at runtime

## Install and run

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
chat-archive-explorer --version
chat-archive-explorer doctor
```

Windows activation:

```powershell
.venv\Scripts\activate
```

The default application directory is resolved with platform conventions. Override it for testing:

```bash
CHAT_ARCHIVE_EXPLORER_DATA_DIR=/tmp/cae-data chat-archive-explorer doctor
```

Machine-readable output:

```bash
chat-archive-explorer doctor --json
```

## Inspect an export source

Inspect a ChatGPT export directory or ZIP without changing the source:

```bash
chat-archive-explorer inspect-export /path/to/export
chat-archive-explorer inspect-export /path/to/export.zip --json
```

The command inventories regular files, rejects unsafe or duplicate normalized paths, reports
known files, and requires `conversations.json` plus `export_manifest.json` at the selected source
root. It then checks that both required files are UTF-8, contain valid JSON, use the expected
top-level JSON type, and satisfy the minimal confirmed source structure. Conversation records need
`id` or `conversation_id`, and `mapping` must be a JSON object. Exit code `0` means all checks
passed; exit code `20` means validation failed. This command does not normalize records, validate
message graphs, or identify an export-format version.

## Development checks

The runtime has no third-party dependencies. Development tools are optional:

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build
```

## Exit codes

- `0`: success
- `2`: command-line usage error
- `10`: configuration error
- `20`: self-check or validation failure
- `70`: unexpected internal failure

Expected errors are displayed without a traceback. Set `--debug` to include exception details in
logs while developing.

## Specifications

Normative project documents are in [`docs/specifications/`](docs/specifications/):

1. Export Format Specification v1.0
2. Architecture Specification v1.0
3. Developer Guide / Project Conventions v1.0
4. Implementation Roadmap v1.0

## Privacy

The application is local-first and offline. Logs must not contain conversation text, attachment
contents, authentication data, or complete raw records by default.
