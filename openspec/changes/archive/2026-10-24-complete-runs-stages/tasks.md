# Tasks

## 1. The shared runner

- [x] 1.1 `src/agentmarshal/stages.py`: `_run_stages` becomes
  `run_stages(placement, state, task_id, commit, base, phase, stderr)`
  returning `StageRunResult(status, pauses, plan_empty)` — the pause
  lines and the no-stage line move to the caller; every other line
  stays inside the runner. `_run_stages` resolves the placement and
  local state, calls the runner and renders the result so `stage run`
  is unchanged byte for byte. Verify: the existing `test_stages.py`
  suite passes untouched.

## 2. `complete` runs the stages

- [x] 2.1 `src/agentmarshal/cli.py`: `_run_complete`'s embedded branch
  establishes the task's open state, resolves `--commit`/`--base` the
  gate's own way, resolves the clone's local state, runs `run_stages`
  for `pre-gate` quiet before `complete_task`, refuses a machinery
  refusal on one `complete:` line, and on a pause decides with
  `git merge-base --is-ancestor` of the resolved candidate into the
  resolved `--target` — not an ancestor, none given or unresolvable:
  one paused line, nothing written, exit 3; an ancestor: one
  `complete: WARNING:` line per paused stage and the completion
  proceeds and writes `completed`. After `completed` prints,
  `run_stages` runs for `post-gate` quiet, its status dropped. The
  findings lane and the sidecar invoke nothing. Verify: pytest.

## 3. Tests

- [x] 3.1 `tests/test_complete_stages.py`: a test per delta-spec
  scenario, each docstring naming the scenario — the pre-gate run
  before the gate, the machinery refusal, the silent empty plan, the
  operational skip, the findings lane and the sidecar, the pause
  refusing an unmerged candidate, the pause line naming every paused
  stage, the merged warning, the accepted pause standing down, the
  post-gate notification ordering and its verdict-neutrality, and the
  shared runner's unchanged `stage run` transcript with both commands
  through the one function. Verify: pytest.

## 4. Change and archive

- [x] 4.1 `openspec/changes/complete-runs-stages/`: proposal.md,
  design.md, tasks.md and the delta spec under
  `specs/extension-stages/` — the ADDED requirements and their
  scenarios.
- [x] 4.2 `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.13.2
  archive complete-runs-stages --yes`, once implementation and tests
  are complete.
