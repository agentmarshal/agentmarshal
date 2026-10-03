## Why

[ADR-0014](../../../../docs/adr/ADR-0014-where-things-live.md) decisions 1, 2, 6
and 7 place a local working log — not evidence and not the journal — under the
clone's local state: appended events, one JSON object per line, one file per
writer, rotated, with retention that may delete prose and prompts.
[ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 7 fixes the record's shape: `{format: 1, at, event, task?, …}` with the
key `event`, not `kind`. Several coming tasks write there — step events, review
prose, check output, extension events — and each would otherwise invent its own
appending, rotation and reading. One file shared by writers would also have to
answer how two processes appending at once keep each other's lines whole.

## What Changes

One module, `process_log.py`, is the one place events are appended and the one
way they are read back. A writer gets a file of its own under the local state's
`log/` directory — the location the CR-148 resolver names — so concurrent
writers never share a line's bytes and need no lock. Events are appended one
JSON object per line in append mode; an event field naming an envelope key is
refused. A file that reaches 10 MiB is renamed with a sequence suffix; at most
five rotated files per writer are kept, the oldest deleted first, and a failed
rotation leaves the file for the next write to retry. Every process run is a
writer, so the directory is bounded as a whole too: a writer that opens
deletes the oldest files past 50 MiB, never one a running writer may still
hold. The reader returns every file's events ordered by `at`, skipping an
unfinished last line and any line that is not a JSON object, keeping event
kinds it does not know as data. The local state's explicit creation call gains
a containment check — it refuses a path outside the local state root — and
creating `log/` goes through it. Nothing calls the module yet; the producers
and consumers are later tasks.

## Capabilities

- new: `process-log`

## Impact

Writers in two processes appending at once can no longer interleave or tear
each other's lines — they never share a file. A reader sees every writer's
events in one `at`-ordered stream, tolerates the torn tail of a still-writing
file and reads rotated files as well as current ones. The gate is untouched
and never reads the log (ADR-0014 decision 3); a test pins that importing the
gate does not import the module.
