## 1. The count line

- [x] 1.1 `run_gate` counts the task's `changes_required` review verdicts
  over `task.records` — every review record of the task's candidates,
  whatever commit it names; a review bound to a research finding
  (`reviewed_finding`, ADR-0009) is not counted — and, on the
  implementation lane only, ends the transcript with the line design.md
  states: `INFO:` below the threshold, `WARN:` when the count has reached
  it — verify: pytest, including a task that carries both kinds of
  review.
- [x] 1.2 The threshold is read with `changes_required_threshold` from
  the journal repository's `project.json`; an unreadable setting lands
  on the line as `threshold unreadable: <error>` and the run continues —
  verify: a test whose `project.json` threshold is malformed sees the
  line and an unaffected run.
- [x] 1.3 The line is a `say`, never a `check`: it adds no violation,
  changes no exit status, refuses no merge — verify: a candidate at the
  threshold with an approving review still passes.
- [x] 1.4 The journal-only lane prints no count line — verify: a test
  naming the scenario, and the embedded journal-only fixture unchanged
  in the diff.

## 2. Tests and fixtures

- [x] 2.1 Every scenario of the new requirement is demonstrated by a test
  whose docstring names it — verify: grep the docstrings.
- [x] 2.2 The implementation-lane fixtures are regenerated through
  `AGENTMARSHAL_UPDATE_GATE_FIXTURES=1` and
  `test_regenerate_the_committed_fixtures`; the fixture diff is exactly
  the new line on the implementation-lane cases and nothing on the
  embedded journal-only case — verify: `git diff tests/fixtures/gate/`.
- [x] 2.3 The pinned-transcript test passes against the regenerated
  fixtures — verify: `uv run pytest` with the update flag unset.

## 3. Archive

- [x] 3.1 `openspec archive gate-changes-required-count` moves the change
  under `openspec/changes/archive/` and lands the delta's requirement in
  `openspec/specs/gate-lanes/spec.md` — verify: the archive command's
  output and the merged spec.
