# Tasks

## 1. The run loop

- [x] 1.1 `src/agentmarshal/stages.py`: `_run_stages` gains a lazy,
  run-cached acceptance read — `read_records` on the placement's
  journal, first tried when a `pre-gate-stop` stage's decision is
  `failed`, `did-not-finish` or `not-run`, a refusal named once on
  stderr naming the journal and answering no acceptance — and the
  match: `accepted_pause` naming the stage's extension,
  `accepted_commit` equal to the resolved commit, the latest in journal
  order. The result line keeps its outcome and adds
  `, pause accepted by <party> (<reason>)` with `accepted_by` and
  `reason` escaped for display; the stage's `extension-event` keeps its
  decision and its reason gains
  `; pause accepted by acceptance record <id>`; the stage does not
  pause. Verify: pytest.

## 2. Tests

- [x] 2.1 `tests/test_stages.py`: a test per delta-spec scenario, each
  docstring naming the scenario — the accepted pause letting the
  process continue naming who accepted, the did-not-finish/not-run
  form, the latest-in-journal-order match, the non-matching bindings
  and forms, another stage's pause standing, the checked,
  pre-gate-warn, post-gate and switched-off stages unchanged, the
  event naming the record, the escape on display and the unreadable
  journal's line with every pause standing. Verify: pytest.

## 3. Change and archive

- [x] 3.1 `openspec/changes/stage-run-accepted-pause/`: proposal.md,
  design.md, tasks.md and the delta spec under
  `specs/extension-stages/` — the ADDED accepted-pause requirement and
  the MODIFIED pause requirement carrying its full text and every
  existing scenario.
- [x] 3.2 `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.13.2
  archive stage-run-accepted-pause --yes`, once implementation and
  tests are complete.
