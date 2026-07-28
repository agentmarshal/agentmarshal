+++
schema = 1
id = "CR-032"
title = "lint the framework source: anchor ruff exclude to the v1 submodule"
scope = ["pyproject.toml", "src/agentmarshal/__main__.py", "src/agentmarshal/doctor.py", "src/agentmarshal/migrate.py", "src/agentmarshal/journal/__init__.py", "src/agentmarshal/journal/backfill.py", "src/agentmarshal/journal/complete.py", "src/agentmarshal/journal/gate.py", "src/agentmarshal/journal/gate_context.py", "src/agentmarshal/journal/records.py", "src/agentmarshal/journal/session.py", "src/agentmarshal/journal/status.py"]
acceptance = []
+++

# CR-032: lint the framework source

## Context

`[tool.ruff] extend-exclude = ["agentmarshal"]` was meant to skip the v1
archive submodule at the repository root (`./agentmarshal/`), but the
pattern matches any path component named `agentmarshal` — so it also
excluded our own `src/agentmarshal/`. CI's `ruff check` and `ruff format
--check` therefore never linted the framework source; only mypy did.
Surfaced during CR-027/029 (per-file ruff flagged E501 that the project
run did not). This closes the gap by anchoring the exclude to the root
submodule, then fixes the violations the change exposes.

## Objective

Make CI lint `src/agentmarshal/` again by anchoring the ruff exclude to the
root-level v1 submodule only, and clean up the previously-unlinted
violations so the project-wide `ruff check` and `ruff format --check` pass.

## Acceptance Criteria

- [ ] `[tool.ruff] extend-exclude` anchors to the root submodule
      (`/agentmarshal`) so `src/agentmarshal/` is linted while the v1
      archive at `./agentmarshal/` stays excluded.
- [ ] Every violation the re-enabled lint AND format check expose in the
      in-scope source files is fixed (import ordering, line length, and
      `ruff format` normalization), with no behavior change — formatting/
      wrapping only. The re-enabled `ruff format --check` covers src too,
      so previously-unformatted files are normalized.
- [ ] `uv run ruff check` and `uv run ruff format --check` (project-wide,
      as CI runs them) pass, and still exclude the v1 submodule.
- [ ] `uv run agentmarshal validate`, pytest, and mypy stay green.

## Non-Goals

- No functional/behavioral change to any module — only lint/format fixes
  and the one config line.
- No change to the v1 submodule or its exclusion in intent (it stays
  unlinted).
- No new ruff rules or config beyond fixing the exclude anchor.
