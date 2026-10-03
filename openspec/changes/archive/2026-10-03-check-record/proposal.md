## Why

ADR-0017 decision 1 and ADR-0022 section 3 put a `check` record in the
0.5.0 record model: a trace of what a pipeline check found on a commit —
its name, its result, the step that failed, a bounded excerpt and a link
to the run — written by whoever observed the run. It is a measurement,
admitted after any terminal record, completed or abandoned. CR-154 laid
down the registry a record type declares through and the shared field
validators; CR-160 showed a schema-7 field family registering. The
journal cannot yet carry a check outcome at all.

## What Changes

- A `check` record type joins the record-type registry, declared once:
  its predicate type, no projected state, admission after `done` and
  `abandoned`, writable, `recorded_by` with `recorded_by_source`
  required.
- Its fields register as a schema-7 field family: `commit` (required,
  exactly 40 lowercase hex), `name` (required non-empty string),
  `result` (required, one of `passed`, `failed`, `error`, `skipped`),
  and optional `failed_step`, `excerpt` and `run_url` (non-empty strings
  when present). `excerpt` registers a 4 KiB UTF-8 byte bound; `name`,
  `failed_step`, `excerpt` and `run_url` register under the
  forgeable-text rule for this record type and field.
- A `check` record stamped below 7 is refused at write and on read; a
  writer stamps 7 through the minimum-schema derivation, and
  `create_check_record` builds the record.

## Capabilities

- added: `review-evidence`
- modified: `record-lifecycle`

## Impact

No other record type changes, and the gate's fixtures are unchanged. The
projection and the gate admit a check append after a terminal record
through the one registry — no second list — while the transcript's
measurements line keeps today's wording until its own task. The
`record-check` command, the excerpt's leak scan at write, the brief's
last failing check and the report count are later tasks.
