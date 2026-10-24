## Context

ADR-0013 decision 2 names the two lifecycle points — `pre-gate` (in CI,
at the merge step, and inside `complete`) and `post-gate` (after
`complete`) — and states the merge-state rule: inside `complete`, a
`pre-gate-stop` pause applies while the candidate is not yet merged
into the target branch and is reported as a warning once it is.
Decision 4 makes `post-gate` a notification. CR-211 through CR-224
built the whole run `stage run` performs: base-materialized manifests
and code, per-stage snapshots, the argv launch under the core's
interpreter, the isolation floor, grants on a workstation, the
switches file at the base, accepted pauses, and the process-log
events.

`complete` today is `_run_complete` in `cli.py` over `complete_task`
in `journal/complete.py`: the task's open state is established, the
gate runs, and only a pass writes `completed`. `stage run`'s
`_run_stages` takes a parsed-args namespace, so nothing but the CLI
command can invoke it.

## Goals

- `complete --task --commit --base` runs the same checks `stage run`
  runs at `pre-gate`, before the gate check and before anything is
  written.
- A `pre-gate-stop` pause refuses the completion while the candidate
  is not an ancestor of the resolved base, and is a warning once it
  is.
- `post-gate` runs after the `completed` record is written; a
  notification, never a verdict.
- A project with no stage-declaring extension — the `complete --findings`
  lane, and the sidecar — sees exactly the `complete` it has today.

## Non-Goals

- Stages from the gate itself or from `review` — ADR-0013 keeps the
  extension a separate step beside the gate; the gate reads none of it.
- Personal extensions — the scopes and the points where a personal
  stage would run are not decided here.
- Any stage beyond `pre-gate` and `post-gate`.

## Decisions

- **The runner is one function, `stages.run_stages`, and the caller
  renders the tail.** `_run_stages` resolves the placement and local
  state, calls the runner, and prints what the result owes `stage
  run`'s transcript — the per-entry pause lines and the no-stage line —
  then returns the result's status. The runner keeps every other line
  inside itself: the stage frames and result lines on stdout, the
  notes, warnings and refusal lines on stderr, each unchanged. The
  result is small: `status` (what the invocation would exit with),
  `pauses` (the `<name>: <result>` entries of the `pre-gate-stop`
  stages that paused, in run order) and `plan_empty`. This is the
  smallest split that lets `complete` render the same pauses two ways
  — refusal or warning — without the runner knowing which command
  called it.
- **`complete` invokes the runner where the task's open state is
  already established.** In `_run_complete`'s embedded branch,
  `load_task_for_record` runs first — the closed-task refusal still
  precedes any extension work, byte for byte — then `local_state`
  resolves the clone's state, then `run_stages` for `pre-gate` runs
  before `complete_task` is entered. A run whose machinery refused
  (status 1) refuses the completion on one `complete:` line; an empty
  plan prints nothing, which is what keeps a project with no
  stage-declaring extension byte for byte what it is today.
- **"Merged" is `git merge-base --is-ancestor` of the resolved
  candidate into the resolved base, in the journal's repository.** The
  references are resolved with the gate's own `_resolve_commit`, the
  way `complete_task` resolves them for `run_gate`. Any answer the
  check cannot produce — a reference gone, a git that will not run —
  reads as not merged: the fallback keeps the pause rather than
  silently lifting it. A merged candidate's `merge-base..candidate`
  range is empty, so the gate then refuses it on its own rule; the
  warning is what the pause becomes, not a pass.
- **`post-gate` runs after `complete`'s own output.** The call sits
  after `completed` prints, so the notification lands last in the
  transcript; its status is dropped — decision 4.
- **The findings lane and the sidecar invoke nothing.** `complete
  --findings` takes no candidate; a sidecar runs no stages, the same
  rule `stage run` enforces — the stage's base is a property of the
  embedded placement.

## Risks

- [A silent lift of the pause] → the merged check fails closed: any
  failure to answer reads as not merged and the pause stands.
- [`stage run`'s transcript drifting from its pin] → the wrapper only
  renders what the result returns; every other line stays inside the
  runner, and the existing `stage run` tests pin the transcript.
- [A no-extension project's `complete` gaining lines] → the empty plan
  returns a marked result and `complete` withholds the no-stage line;
  the existing complete tests pin the transcript.
- [An early return skipping an owed line] → the pause entries are
  returned, not printed, so the caller cannot reach a branch where the
  lines were already spent or never emitted.
