# CR-014: `agentmarshal doctor` — onboarding health check

Owner: lead
Type: feat
Priority: P2
Created: 2026-07-19
Status: open
Scope:
- .agentmarshal/journal/tasks/open/CR-014-doctor.md
- src/agentmarshal/
- tests/

## Context

Onboarding (founding brief §4.2-5) needs a health check that tells the
operator what is wrong before a task ever runs. The v1/v2 bootstrap
retros catalogued the failures a `doctor` must catch early: missing git,
an uninitialized project, an unresolvable project root. Each check
reports an actionable line; the exit code is non-zero if any check
fails. Keep it a diagnostic — `doctor` never changes state.

Design constraints (binding):

- Standard library only; the only external process is `git`
  (`git --version` and `git rev-parse`); `pathlib`; explicit
  `encoding=`; each check fails closed with a clear, actionable message.
- Reuse project discovery (`find_project_root`) and the project-file
  reader (`read_project_file`); do not reimplement them.
- Checks are data-driven: a list of named checks each returning
  ok/failed plus a message, so future checks are added without
  restructuring.

## Objective

`agentmarshal doctor` reports the health of the current repository's
AgentMarshal setup and exits non-zero on any failure.

## Acceptance Criteria

- [ ] `agentmarshal doctor` runs a set of checks and prints one
      `OK: <name> — <detail>` or `FAIL: <name> — <detail>` line each,
      then a final summary line; exit 0 only if every check passed.
- [ ] Checks included: `git` available (invokes `git --version`, fails
      closed if the executable is missing); inside a git repository
      (uses `find_git_root`); project initialized (a readable
      `.agentmarshal/project.json` discovered from the cwd); project
      schema is understood (the file parses and its `schema` is `1`).
- [ ] Each check is independent: a later check still runs and reports
      even if an earlier one failed, unless it strictly depends on the
      earlier result (a missing project file makes the schema check
      `FAIL`, not a crash).
- [ ] Fail-closed: outside a git repository, without a project file, or
      with a malformed/unknown-schema project file, `doctor` reports the
      specific failure and exits non-zero; it never raises a traceback.
- [ ] Tests cover: all checks passing in an initialized repo (exit 0);
      outside a git repo (git-repo and project checks FAIL, exit 1);
      initialized git repo without a project file (project check FAIL);
      a project file with an unknown schema (schema check FAIL); a
      malformed JSON project file (schema check FAIL, no traceback);
      git-missing simulated via a stubbed executable resolver.
- [ ] `uv run pytest`, `ruff check`, `ruff format --check` and `mypy`
      are green locally and in CI on the reviewed SHA.

## Non-Goals

- No provider/secret/runner-image checks (they need provider wiring, a
  later slice), no auto-fix or state changes, no CI-template
  generation.
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
