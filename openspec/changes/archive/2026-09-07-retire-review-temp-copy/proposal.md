## Why

CR-091 made the reviewer's prose a pinned journal artifact, but left three
edges its reviews named: the launcher still copies the same bytes into the
system temp directory on every accepted verdict with findings (prose leaking
outside the placement that decides publication); a record refused after its
artifact was written leaves an orphan in an append-only directory; and the
gate's path-collision check covers records but not artifacts. The baseline
spec also promises `report` a per-record count it cannot show.

## What Changes

- `agentmarshal review` keeps no temp copy of prose it has pinned; the
  operator is told the artifact's path only. A rejected verdict still keeps
  its output outside the journal, as today.
- A review record that the writer would refuse for a reason it can check
  before writing — shape, binding, task, identity — is refused before its
  artifact is written; one function states those checks and both writers
  use it.
- The gate refuses a candidate that adds an artifact path already present in
  the base tree, as it does for a record path.
- The `review-evidence` spec says what `report` shows: the task's total.
- **BREAKING** for scripts that parsed `reviewer output kept at` on success:
  the line is gone on that path (it stays on the rejected-verdict path).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `review-evidence`: the accepted-verdict path keeps no copy outside the
  journal; a refused record leaves no artifact behind; artifact paths follow
  the record collision rule; `report` shows the task total.

## Impact

`src/agentmarshal/journal/review.py`, `submit_review.py`, `records.py`
(one pre-write refusal used by both writers), `gate.py` (collision check
over artifacts), `cli.py` (stderr line), docs (quickstart, overview sentence
on the temp file), the operator's `am-land` (greps `kept at`; outside the
repository).
