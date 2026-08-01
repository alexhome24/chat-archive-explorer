# DEVELOPMENT_WORKFLOW.md

# Development Workflow

This document describes the established day-to-day development workflow
of Chat Archive Explorer. It supplements the existing specifications and
does not replace or modify them.

## 1. Source of Truth

-   The GitHub repository is the **single source of truth** for the
    project.
-   All development is based on the current state of the `main` branch.
-   Temporary ZIP archives are working copies only and never replace the
    repository.

## 2. Local Working Environment

The project owner maintains one permanent local working copy containing:

-   `.git`
-   one persistent `.venv`
-   all development tools
-   the complete project history

This working copy is the only location where acceptance is performed.

## 3. Developer Deliverables

When implementation is performed outside the owner's environment, the
developer provides:

-   modified files;
-   new files;
-   deleted files (if any);
-   tests;
-   documentation updates;
-   engineering report.

If a ZIP archive is used, it is treated only as a transport mechanism.

## 4. Integrating a Working Archive

Files from a developer archive are copied into the permanent Git working
copy.

The following directories and files are **never** copied from a working
archive:

-   `.git/`
-   `.venv/`
-   `dist/`
-   `build/`
-   `*.egg-info/`
-   `__pycache__/`
-   `.pytest_cache/`
-   `.mypy_cache/`
-   `.ruff_cache/`

The permanent Git working copy always remains the authoritative local
workspace.

## 5. Working Tree Status

Before starting local acceptance, the permanent Git working copy must be
clean.

``` bash
git status
```

If the working tree is not clean, the reason must be understood before
continuing.

## 6. Mandatory Acceptance Checks

Every Slice and every Milestone must pass the following checks in the
permanent Git working copy:

``` bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build
```

In addition, all CLI smoke tests introduced by the implemented Slice
must succeed.

## 7. Sandbox Limitations

If an engineering tool is unavailable in the implementation environment
(for example Ruff, mypy or build):

-   the developer MUST explicitly state that the tool could not be
    executed;
-   the developer MUST NOT claim that the corresponding check passed;
-   the developer MUST NOT attempt to reproduce tool behaviour manually.

These checks are completed only during local acceptance.

## 8. Automatic Formatting

Running

``` bash
python -m ruff format .
```

before acceptance is allowed and encouraged.

Automatic formatting:

-   does not change functionality;
-   does not require a repeated functional engineering review;
-   may be committed together with the current Slice if it is the only
    remaining acceptance issue.

## 9. Acceptance and Publication

After successful local acceptance:

``` bash
git add .
git status
git commit
git push origin main
git tag -a <tag> -m "<message>"
git push origin <tag>
```

Each accepted Slice or Milestone is committed using a separate
Conventional Commit.

Tags are created only for accepted Milestones or explicitly accepted
Slice releases, according to the project's versioning policy.

## 10. Sequential Development

The next Slice MUST NOT begin until the previous Slice has been:

-   accepted locally;
-   committed;
-   pushed to GitHub;
-   tagged (when applicable).

Only then does implementation continue.

## 11. Engineering Reports

Each Slice engineering report must explicitly distinguish between:

### Verified in the implementation environment

Checks actually executed by the developer.

### Verified during local acceptance

Checks executed by the project owner in the permanent Git working copy.

This distinction is mandatory for every future Slice and Milestone.

## 12. Lessons Learned

Experience gained during accepted Milestones may be incorporated into
this workflow to improve future development.

This document describes the current agreed workflow and may evolve only
after practical experience, not speculative planning.
