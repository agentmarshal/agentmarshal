+++
schema = 1
id = "CR-030"
title = "forward-capture flip: live records emit schema 2, migration marks imported"
scope = ["src/agentmarshal/journal/records.py", "src/agentmarshal/migrate.py", "tests/test_journal.py", "tests/test_migrate.py"]
acceptance = []
+++

# CR-030: forward-capture flip

## Context

CR-027 added record schema 2 (provenance-carrying, in-toto-Statement
projectable) as a non-breaking superset of schema 1, but deferred flipping
forward capture to it because the `create_*` builders are shared by many
call sites, including `migrate` (CR-027 non-goal, contract amendment).
This is that flip: new live records become in-toto-complete from the
start, and migrated (imported) records carry the honest
`imported-from-host` provenance ADR-0005 Decision 4 requires. Existing
schema-1 records in the journal stay valid (grandfathered by CR-027).

## Objective

Make the `create_*` record builders emit schema 2 with a `source`
provenance field (default `live`), and make v1->v2 migration mark its
records `imported-from-host`, so forward capture is in-toto-complete and
provenance is honest — without changing any other call site (open,
submit-review, complete, record-session pass the default) or breaking the
existing journal.

## Acceptance Criteria

- [ ] Every `create_*` builder in `records.py` emits `schema` 2 and a
      `source` field, and accepts an optional keyword `source` defaulting
      to `SOURCE_LIVE`. The emitted records validate (they satisfy the
      schema-2 provenance rules CR-027 added).
- [ ] `migrate.py` passes `source=SOURCE_IMPORTED` for every record it
      builds (opened, review, completed, abandoned, and the review-parse
      validation probe), so migrated evidence is labelled
      `imported-from-host`, not `live`.
- [ ] The live call sites (`open_task`, `submit_review`, `complete`,
      `record-session`) are unchanged and inherit the `live` default; no
      new parameter is threaded through them.
- [ ] `agentmarshal validate` stays green on the existing journal
      (schema-1 history plus new schema-2 records), and the full suite,
      ruff, format, and mypy stay green.
- [ ] Tests: a `create_*` builder emits schema 2 / `source = live` and its
      record round-trips; a migrated journal's records are schema 2 with
      `source = imported-from-host`.

## Non-Goals

- No backfill of historical economics — that is CR-031, which consumes the
  now-flipped `create_session_record(source=...)`.
- No in-toto/DSSE/Sigstore projection (wave 2).
- No rewrite of existing schema-1 records; they remain valid as-is.
- No change to the record schema itself (CR-027) or the capture policy
  (CR-029).
