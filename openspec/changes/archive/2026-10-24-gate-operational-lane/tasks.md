# gate-operational-lane — Tasks

## 1. The lane predicate

- [x] 1.1 `_extension_names_at_tree` splits the enumeration half out of
  `stages.py`'s `_base_extensions` into `gate.py` — the shared
  extension names a tree declares plus which are directory-form — and
  `_base_extensions` delegates to it, behaviour unchanged — verify:
  the existing stages tests (pytest).
- [x] 1.2 `operational_candidate(project_root, task_id, merge_base,
  resolved_commit, changes_with_status)` returns the contract the lane
  is judged under or `None`: `.agentmarshal/switches.toml` changed,
  every other changed path under `.agentmarshal/journal/tasks/<task>/`,
  and the task's contract — read from the merge-base tree when present
  there, else from the candidate's tree — parsing and declaring scope
  exactly `[".agentmarshal/switches.toml"]` — verify: the scenario
  tests (pytest).

## 2. The gate

- [x] 2.1 `run_gate` asks the predicate only when `not sidecar` and runs
  the lane block when it returns a contract: the PASS line, the
  switches checks against the base-declared names, NOT EXAMINED for
  agreement, latest review and reviewer independence, NOT EXAMINED per
  declared independence rule and for declared reviewers when the
  contract declares them, and the named-documents and implementers
  checks as today — verify: the scenario tests (pytest).
- [x] 2.2 The `changes_required` count line is suppressed on the
  operational lane exactly as on the journal-only lane — verify:
  pytest.
- [x] 2.3 The journal-only, findings, regular and sidecar lanes print
  byte-for-byte what they print today — verify: the pinned transcript
  fixtures unchanged (pytest).

## 3. `stage run`

- [x] 3.1 `stage run --phase pre-gate` calls the gate's
  `operational_candidate` after the merge base is computed and before
  extensions are enumerated; on a contract it prints
  `stage run: pre-gate stages do not run on an operational change`,
  runs nothing and exits 0; other phases and candidates are unchanged —
  verify: the scenario tests (pytest).

## 4. The change itself

- [x] 4.1 proposal.md, design.md, tasks.md and the gate-lanes delta spec
  are written — verify: openspec validate.
- [x] 4.2 Every scenario in the delta spec is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the spec's scenario headings.
- [x] 4.3 Full check sequence passes: `uv run agentmarshal validate`,
  `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`,
  `uv run mypy` — and the CI-conditions run `env -u AGENTMARSHAL_ACTOR
  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 uv run pytest -q`.
- [x] 4.4 The change is archived with the archive command — verify:
  `openspec/specs/gate-lanes/spec.md` gains each new requirement once
  and the change lives under `openspec/changes/archive/`.
