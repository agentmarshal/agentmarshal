## Why

[ADR-0013](../../../../docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
decision 2 gives the two stages a second invocation point: inside
`complete`, which may run before or after the implementation merges —
a `pre-gate-stop` pause applies while the candidate is not yet merged
into the target branch and is reported as a warning once it is, and
`post-gate` is a notification after `complete`. CR-211 built
`stage run`, CR-217 the switches, CR-221/CR-223 the isolation, CR-224
the accepted pauses — but `complete` still invokes none of it: a
`pre-gate-stop` extension can pass a candidate through `stage run`,
then watch the same candidate complete untouched by the check.

## What Changes

- `stages.py`'s `_run_stages` becomes `run_stages`, a function taking
  the placement, the clone's local state, the task, the commit, the
  base, the phase and stderr explicitly and returning a small result —
  the status the invocation ends with, the pauses that stand, whether
  the plan came up empty. The per-entry pause lines and the no-stage
  line move to the caller; `stage run`'s wrapper renders them so the
  command is unchanged byte for byte.
- `complete --task --commit --base` (the embedded placement) runs the
  runner for `pre-gate` before its gate check and before anything is
  written. A pause decides on `git merge-base --is-ancestor`: while
  the candidate is not an ancestor of the resolved base the completion
  is refused with the pause status; once it is, each pause prints as a
  warning and the completion proceeds.
- After the `completed` record is written, `complete` runs the runner
  for `post-gate`; a post-gate result changes neither the record nor
  the exit status.
- `complete --findings` and the sidecar placement run no stage; a
  project whose shared extensions declare no stage reads exactly as
  `complete` reads today.

## Capabilities

- modified: `extension-stages`

## Impact

`stages.py` splits its run into the shared runner and the `stage run`
wrapper; `cli.py`'s `_run_complete` gains the two invocations and the
merge-state check. `journal/complete.py` and the gate are untouched —
the gate reads nothing of a stage's run and decides nothing new. No
other command changes.
