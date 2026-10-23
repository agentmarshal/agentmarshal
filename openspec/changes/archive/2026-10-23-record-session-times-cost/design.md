## Context

CR-176 registered `started_at`, `ended_at`, `resets_at` and `cost` in
the schema-7 session family: `create_session_record` accepts them as
optional keyword arguments and the `session-fields-7` rule owns every
refusal — a lone start or end, an end earlier than the start, a
non-UTC or malformed timestamp, a reset time off a `provider-limit`
outcome, a malformed `cost` object. CR-166 is the pattern for putting a
family field behind a flag: `record_session` gains optional keyword
arguments and passes them through, and the record rules stay the only
judge of a value. What remains is the writer surface for the four
fields — plus the idempotency flag ADR-0019 decision 6 decided, because
recording cost after completion was measured to double a task's cost on
a retry.

## Goals

- `record-session` writes every remaining field of the schema-7 session
  family from flags: `--started-at`/`--ended-at` (both or neither),
  `--resets-at`, and the cost trio `--cost-amount`, `--cost-currency`,
  `--cost-source` (all three or none).
- Every refusal a flag value earns names the flag and lands before
  anything is written.
- `--if-missing` makes a repeat write under the same
  `task + role + actor + activity` a no-op that prints one line naming
  the existing record.
- Nothing existing changes: no flag, no field, no printed line; a
  session recorded without the new flags is byte-for-byte the record
  the command wrote before them, apart from id and times.

## Non-Goals

- `report` showing lead time, phases or per-currency sums — a later
  task, as the ADR's non-goals state.
- Converting currencies or checking an amount against a price list.
- Raw provider exports to the process log.
- Any check that a cost's figure is true (docs/threat-model.md: what
  the journal checks is shape, not truth).

## Decisions

- **`record_session` gains the values as optional keyword arguments and
  passes them to `create_session_record`** — the `usage` pair's own
  pattern, and CR-165's for this same family. The cost arrives
  flag-shaped — `cost_amount`, `cost_currency`, `cost_source` — and the
  `{"amount", "currency", "source"}` object is assembled at the
  boundary, so "all three or none" is checked where the flags are
  known, never by matching a half-built object.
- **Flag-named refusals restate the record rule before writing** — the
  `reviewer_actor_refusal` pattern: what the operator typed was a flag,
  so a refusal names `--started-at`, `--ended-at`, `--resets-at`,
  `--cost-amount`, `--cost-currency` or `--cost-source`, not the record
  field. The same predicates the rule runs decide: `_utc_timestamp`
  for the timestamps — the flag name is passed as its `what`, so the
  refusal is literally the rule's own words — and the `_COST_AMOUNT` /
  `_COST_CURRENCY` patterns; `--cost-source` carries `choices` like
  `--usage-method`, so argparse names the flag on a word outside the
  vocabulary. Grouping is checked before shape: an unpaired time or an
  incomplete trio is named as such; then an early end, a `resets_at`
  off `provider-limit`, and each malformed value.
- **`--if-missing` matches inside `record_session`, on the records
  `load_task_for_record` already loaded.** The deduplication key is
  `task + role + actor + activity` exactly (ADR-0019 decision 6, whose
  "Alternatives considered" records why a wider key lost roles): the
  first session record in stored order with the same three fields makes
  the write a no-op and its id is returned for the message; every other
  field — outcome, tokens, times, cost — is ignored, and a second task
  is out of the match by construction. A repeat with malformed flags is
  still refused: the flag checks run before the match. `record_session`
  returns a small result — the written path, or the existing record's
  id — so the command prints the path as today on a write, and one line
  naming the existing record on a no-op.
- **Without the new flags nothing changes.** Each value lands only when
  supplied, so a session recorded with the earlier flags is the record
  the previous release wrote, `created_at` and id aside — the pin the
  byte-for-byte scenario holds.

## Risks

- [A repeat under `--if-missing` writes a second record anyway] → the
  match runs on the task's validated records before `create_session_record`
  is called, and the no-op test counts the task's session records.
- [Flag-named refusals drift from the record rules] → the helper calls
  the rule's own predicates where they exist (`_utc_timestamp`, the two
  cost patterns) and the write still passes the rules themselves: the
  flag layer can only refuse earlier, never admit.
- [A session written before the fields existed blocks `--if-missing`]
  → it does not: the match reads `role`, `actor` and `activity`, which
  every session record carries, whatever its schema.
- [A legitimately different session shares the triple] → intended by
  ADR-0019: that is the deduplication key the decision chose, and the
  flag is opt-in — nothing matches unless `--if-missing` is given.
