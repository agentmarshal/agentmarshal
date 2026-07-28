+++
schema = 1
id = "CR-031"
title = "backfill tool: import historical economics as imported-from-host session records"
scope = ["src/agentmarshal/journal/backfill.py", "tests/test_backfill.py"]
acceptance = []
+++

# CR-031: backfill tool

## Context

The journal-revision audit found token economics were never durable: they
live only in gitignored v1-format stat records
(`.agentmarshal/journal/runs/stats/RUN-*.json`), lost on re-clone. ADR-0005
Decision 4 sanctions a retroactive backfill that imports retained host
data into the journal as provenance-marked records. CR-027 added the
schema-2 `source` field, CR-028 lets session records accrue after a
terminal record, and CR-030 flipped `create_session_record` to schema 2 —
so the pieces exist. This slice builds the mapping library that turns a v1
stat record into a schema-2 `session` record marked
`imported-from-host`, preserving the original timestamp.

The library is pure mapping + validation; it writes nothing to the
journal. The actual restore run (writing the records per task through the
measurements lane and committing) consumes this library and is a separate
data operation.

## Objective

Provide a deterministic, tested mapping from retained v1 stat records to
schema-2 `imported-from-host` session records, so the historical economics
can be restored into the journal without being mislabelled as live.

## Acceptance Criteria

- [ ] `src/agentmarshal/journal/backfill.py` reads v1 stat records from a
      stats directory, tolerating unrelated files, and maps each to a
      schema-2 `session` record: `source = imported-from-host`,
      `created_at` = the stat's original `recorded_at` (not now), tokens
      taken from the stat (cache = cache-read plus cache-creation so no
      token is dropped), `activity` normalized to the session vocabulary
      (implementation / review / other), and `actor` derived from the
      stat's vendor and model.
- [ ] Each produced record is validated against the record schema before
      it is returned, so a malformed mapping fails closed rather than
      producing an invalid record.
- [ ] A per-task selector returns only the session records for a given
      task id, in a deterministic order (by original timestamp then id).
- [ ] The importer is honest about provenance: every produced record is
      `imported-from-host`, never `live`; this is asserted, not incidental.
- [ ] Tests in `tests/test_backfill.py` cover: a lead and a qa stat map to
      the expected session record (fields, token sums, activity mapping,
      preserved timestamp, imported provenance); unrelated files in the
      stats directory are ignored; a malformed stat fails closed; the
      per-task selector filters and orders correctly.
- [ ] `uv run agentmarshal validate`, pytest, ruff, format, and mypy stay
      green.

## Non-Goals

- No writing to the journal and no git operations: this is a pure mapping
  library. The restore run (per-task measurements-lane commits) is a
  separate data operation that uses it.
- No import of free-text artifacts (review/prompt text): only the
  structured economics. Artifact-text import with mandatory leak-scan
  (CR-029) is a later extension.
- No CLI wiring in this slice (no `cli.py` change).
- No in-toto/DSSE projection (wave 2).
