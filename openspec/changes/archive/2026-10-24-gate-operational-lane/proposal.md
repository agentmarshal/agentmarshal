# gate-operational-lane

## Why

ADR-0013 decision 17 gives the gate a third lane — the operational lane
— and it is not implemented. A shared extension is switched off only by
an operational CR: a candidate whose diff touches only
`.agentmarshal/switches.toml` and its own task's records requires no
review, and a broken extension's `pre-gate` stages must not run for the
candidate that switches it off — deciding to drop an extension cannot
depend on that extension still working. Today every such candidate
takes the regular lane, so switching off a broken extension is refused
for want of a review and its `pre-gate-stop` stage can pause the
transaction that retires it.

## What Changes

- In the embedded placement, a candidate whose changes from the merge
  base are `.agentmarshal/switches.toml` and otherwise nothing outside
  `.agentmarshal/journal/tasks/<task>/` takes the operational lane when
  the task's contract — read from the base tree when the task exists
  there, from the candidate's tree when the candidate opens the task —
  declares `scope` exactly `[".agentmarshal/switches.toml"]`.
- On that lane the transcript prints one PASS line for the transaction
  and one for the scope the lane's own predicate enforces,
  parses the candidate's switches file with CR-217's parser against the
  shared extension names the base declares, and marks the review,
  verdict, independence and agreement checks NOT EXAMINED — the
  operational change requires none of them — while every check that
  does not depend on a review runs as it does today. The file is
  compared to the base's as raw TOML — every top-level key outside
  `switches` identical, and an entry's raw table deciding "changed",
  so a key the parser does not read cannot hide a change. Every entry
  the candidate adds or changes must name this task; an entry the base
  held and the candidate drops refuses the candidate naming the file
  and the entry, and switching an extension back on is a `state = "on"`
  entry naming this task — every change carries the task that made it.
  The lane also requires the base's own switches file to parse: a base
  the read or the parse refuses keeps the candidate off the lane and
  needing a review, since removals and unchanged entries cannot be
  judged against it. In a sidecar the operational lane is not offered.
- `stage run --phase pre-gate` on a candidate the gate's own predicate
  qualifies for the lane prints one line saying pre-gate stages do not
  run on an operational change, runs no stage and exits 0, decided by
  the same function the gate uses — imported, not copied.
- The journal-only, findings and regular lanes print the transcript
  they print today, byte for byte.

## Capabilities

- modified: `gate-lanes`, `extension-stages`

## Impact

`src/agentmarshal/journal/gate.py` gains the lane's predicate — for
example `operational_candidate` — which `src/agentmarshal/stages.py`
imports for its `pre-gate` skip; the switches file and the
base-or-candidate contract are read from trees with the gate's existing
`git show`/`ls-tree` helpers. `tests/` gains a scenario per delta-spec
scenario. `openspec/changes/archive/`,
`openspec/specs/gate-lanes/spec.md` and
`openspec/specs/extension-stages/spec.md` change only through the
archive command.
