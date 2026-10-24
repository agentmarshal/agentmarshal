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

Amended 2026-10-24 (review round 1): merged-ness is decided against a
new `complete --target <ref>` — the branch the candidate merges into —
not against `--base`: a merge wrapper passes the pre-merge merge base
as `--base` even after the merge, so the candidate is never its
ancestor, and passing the target as `--base` makes the gate refuse an
empty range. And `complete` invokes the runner in a quiet mode: the
refs are resolved by `complete` itself before the runner is called, a
plan matching no stage prints nothing at all — no operational line
either — and the run's own refusals carry `complete`'s prefix.

## Goals

- `complete --task --commit --base` runs the same checks `stage run`
  runs at `pre-gate`, before the gate check and before anything is
  written.
- A `pre-gate-stop` pause refuses the completion while the candidate
  is not an ancestor of the resolved `--target` — or no `--target` is
  given — and is a warning once it is.
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
  already established, and quiet.** In `_run_complete`'s embedded
  branch, `load_task_for_record` runs first — the closed-task refusal
  still precedes any extension work, byte for byte — then `--commit`
  and `--base` are resolved with the gate's own `_resolve_commit`, so
  a reference that does not resolve keeps the refusal `complete` gives
  it today rather than surfacing under the stage machinery's voice;
  then `local_state` resolves the clone's state, then `run_stages` for
  `pre-gate` runs before `complete_task` is entered, handed the
  resolved SHAs and `quiet=True`. A run whose machinery refused
  (status 1) refuses the completion on one `complete:` line; an empty
  plan prints nothing, which is what keeps a project with no
  stage-declaring extension byte for byte what it is today — and the
  same holds on an operational candidate, where the quiet runner
  prints the operational line only when a stage would otherwise have
  run (it weighs the base's manifests to learn that; a manifest the
  base cannot parse still counts as a stage that may exist, since the
  lane exists so a broken extension cannot block its own switching
  off). Under quiet the runner's refusals and diagnostics carry the
  calling command's prefix.
- **"Merged" is `git merge-base --is-ancestor` of the resolved
  candidate into the resolved `--target`, in the journal's
  repository.** `--target` names the branch the candidate merges
  into — distinct from `--base`, which stays the merge base the gate
  diffs against, because a merge wrapper passes the pre-merge merge
  base even after the merge. The references are resolved with the
  gate's own `_resolve_commit`, the way `complete_task` resolves them
  for `run_gate`. No `--target`, or any answer the check cannot
  produce — a reference gone, a git that will not run — reads as not
  merged: the fallback keeps the pause rather than silently lifting
  it. A merged candidate proceeds to the gate on the `--base` range,
  which is non-empty exactly because `--base` is the pre-merge merge
  base — the warning is what the pause becomes, and the completion
  writes `completed` when the gate passes.
- **`post-gate` runs after `complete`'s own output.** The call sits
  after `completed` prints, so the notification lands last in the
  transcript; its status is dropped — decision 4.
- **The findings lane and the sidecar invoke nothing.** `complete
  --findings` takes no candidate; a sidecar runs no stages, the same
  rule `stage run` enforces — the stage's base is a property of the
  embedded placement.

## Risks

- [A silent lift of the pause] → the merged check fails closed: no
  `--target` and any failure to answer read as not merged and the
  pause stands.
- [A bad ref or an operational change gaining stage lines under
  `complete`] → `complete` resolves the refs itself first, and the
  quiet mode keeps the no-stage project — ordinary or operational —
  byte for byte; the existing complete tests pin the transcript.
- [`stage run`'s transcript drifting from its pin] → the wrapper only
  renders what the result returns; every other line stays inside the
  runner, and the existing `stage run` tests pin the transcript.
- [A no-extension project's `complete` gaining lines] → the empty plan
  returns a marked result and `complete` withholds the no-stage line;
  the existing complete tests pin the transcript.
- [An early return skipping an owed line] → the pause entries are
  returned, not printed, so the caller cannot reach a branch where the
  lines were already spent or never emitted.
