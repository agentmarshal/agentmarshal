## Why

[ADR-0014](../../../../docs/adr/ADR-0014-where-things-live.md) decisions 1 and
11 place review prose at capture level `hash` — where the journal keeps the
hash, not the prose — and reviewer diagnostics at any level in the process
log, and
[ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 7 names the events: `review-prose` carrying the path to the prose
file and its sha256, and `review-diagnostics`. Today the launcher keeps both
in a local temporary file, because the durable private store the `hash`
level names did not exist. CR-148 built the local state and CR-153 built the
log, so the place the decisions name is real now.

## What Changes

- At capture level `hash`, `agentmarshal review` writes the accepted
  verdict's output byte for byte to a file under the local state's
  process-log area of the repository that holds the journal, and appends a
  `review-prose` event carrying the task, the file's path and its sha256.
  The journal still holds nothing about the prose — no artifact, no field —
  and stderr names the path as it names the temporary file today.
- Whatever a successful reviewer command wrote to its error stream is kept
  the same way at every capture level — file under the process-log area,
  `review-diagnostics` event naming it — instead of a temporary file.
- When the local state cannot be used — git cannot name it or its directory
  cannot be created — the output falls back to a temporary file as today,
  and stderr says why. In a sidecar the files and the events land in the
  journal repository's local state; the host's is never touched.
- The process log gains a payload area — `log/files/` — for files its
  events name, beside the writer files rather than among them.

## Capabilities

- modified: `review-evidence`, `reviewer-adapter`

## Impact

A review's prose at `hash` and a successful reviewer's diagnostics are no
longer bound to the temporary directory — they sit beside the process log of
the clone that recorded the review, and the log says where. Retention of
those files beyond the log's existing bound is a non-goal (CR-153); nothing
reads them back. Levels `commit` and `off` and the rejected-verdict copy are
unchanged.
