# Chat Archive Explorer

Local, offline tooling for turning a ChatGPT export into a durable, searchable archive.

## Project status

Milestone **M0** and the first vertical slice of **M1** are implemented. The repository provides
a runnable CLI, configuration, structured diagnostics and logging, filesystem self-checks, safe
read-only directory/ZIP source adapters, and structural export inventory. It does **not** parse
ChatGPT JSON, build conversations, or persist imported data yet.

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

Inspect a ChatGPT export directory or ZIP without parsing JSON or changing the source:

```bash
chat-archive-explorer inspect-export /path/to/export
chat-archive-explorer inspect-export /path/to/export.zip --json
```

The command inventories regular files, rejects unsafe or duplicate normalized paths, reports
known files, and requires `conversations.json` plus `export_manifest.json` at the selected source
root. Exit code `0` means the source passed this structural check; exit code `20` means the source
could not be opened safely or required files are missing. Passing this check does not yet confirm
JSON validity or an export-format version.

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
