# CR-001: `agentmarshal init` vertical slice and package CI job

Owner: lead
Type: feat
Priority: P1
Created: 2026-07-19
Status: in_review
Scope:
- .agentmarshal/journal/tasks/open/CR-001-init-vertical-slice.md
- gitflic-ci.yaml
- pyproject.toml
- uv.lock
- README.md
- src/agentmarshal/
- tests/

## Context

The repository contains the project skeleton: an empty `agentmarshal`
package with a version string, toolchain configuration (uv, ruff, mypy
strict, pytest) and a CI file with the governance job. This task cuts the
first vertical slice of the product CLI and wires the package checks into
CI so that every later change rides a green pipeline.

Design constraints that apply to all v2 code, starting now:

- Standard library only; no new runtime dependencies in this task.
- No shell-outs to POSIX utilities. The only external process core code
  may ever invoke is `git`; this task needs none.
- `pathlib` for all path handling; every `open()` passes `encoding=`.
- Files are written as UTF-8 without BOM with LF line endings; reads
  tolerate UTF-8 with BOM.

## Objective

`agentmarshal init` initializes a repository for AgentMarshal by creating
`.agentmarshal/project.json`, with explicit project-root discovery and
fail-closed behavior; the package checks run in CI.

## Acceptance Criteria

- [ ] `pyproject.toml` declares an `agentmarshal` console script;
      `uv run agentmarshal --version` prints the package version.
- [ ] `agentmarshal init`, run from anywhere inside a git repository that
      is not yet initialized, creates `<repo-root>/.agentmarshal/project.json`
      containing at least `{"schema": 1, "framework": {"version": ...}}`
      where the version equals the installed package version. The file is
      UTF-8 without BOM, LF line endings, ends with a newline.
- [ ] Project-root discovery walks up from the current directory looking
      for `.agentmarshal/project.json` (the way git discovers `.git`) and
      is a reusable function, not logic inlined in the command.
- [ ] `agentmarshal init` in an already-initialized project (from the
      root or any subdirectory) fails with a message naming the existing
      project root, exits non-zero and modifies nothing.
- [ ] `agentmarshal init` outside any git repository fails with a clear
      message, exits non-zero and creates nothing (fail-closed).
- [ ] Tests cover: fresh init; re-init refusal; init from a subdirectory;
      outside-git failure; discovery through a directory with a Cyrillic
      name; reading a `project.json` that starts with a UTF-8 BOM.
- [ ] `gitflic-ci.yaml` gains a `python` job running, under `PYTHONUTF8=1`:
      `uv sync --locked`, `pytest`, `ruff check`, `ruff format --check`,
      `mypy` — with the same branch/MR rules as the governance job.
- [ ] All checks are green locally and the MR pipeline is green on the
      reviewed SHA.

## Non-Goals

- No `doctor`, git hooks, `.gitignore`/`.gitattributes` editing, host CI
  templates, harness adapters, provider adapters or version handshake —
  later slices.
- No interactive prompts; `init` is non-interactive in this slice.
- Do not modify the `agentmarshal/` submodule.
