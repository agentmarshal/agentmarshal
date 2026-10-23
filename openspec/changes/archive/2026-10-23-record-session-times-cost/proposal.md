## Why

ADR-0019 decides what a session can say about time and money: its start
and end beside `created_at`, which stays the write time (decision 1);
the provider's stated reset time on a `provider-limit` session
(decision 3); an optional cost — amount, currency, source — beside its
tokens (decision 4); and that cost recording after completion is
idempotent (decision 6). ADR-0022 section 2 names the fields, and CR-176
landed them in the record model — `create_session_record` accepts them
and the record rules refuse their malformed shapes. The command does
not expose them yet: the harness records sessions with `record-session`,
which today writes none of them, and a repeated accounting step can
still double a task's cost.

## What Changes

- `record-session` accepts `--started-at <ts>` and `--ended-at <ts>` —
  both or neither — `--resets-at <ts>`, and `--cost-amount <amount>`
  with `--cost-currency <code>` and `--cost-source reported|estimated` —
  all three or none — writing `started_at`, `ended_at`, `resets_at` and
  `cost` through `create_session_record`'s parameters. A session
  recorded with any of them stamps schema 7, as any record carrying the
  family does.
- A value the record rules refuse — an unpaired time, an end earlier
  than the start, a timestamp that is not UTC ISO-8601, a reset time on
  an outcome other than `provider-limit`, an incomplete or malformed
  cost — is refused before writing, the refusal naming the flag, and
  nothing is written.
- `record-session --if-missing` makes a repeat write under the same
  `task + role + actor + activity` a no-op that prints one line naming
  the existing record, and writes as usual otherwise — ADR-0019
  decision 6.
- Without the new flags the command writes and prints exactly what it
  does today.
- The `record-session` flags requirement in `session-activity` is
  modified in place under its exact header: its enumeration of the
  family's fields written from flags becomes incomplete, and "a session
  recorded with none of them keeps the schema it had" becomes untrue the
  moment the new flags exist.

## Capabilities

- modified: `session-activity`

## Impact

`record_session` gains the flag-shaped values as optional keyword
arguments, turns the record rules' refusals into flag-named refusals
before anything is written — the `--actor` pattern — and matches an
`--if-missing` repeat on the task's already-loaded records. The gate's
fixtures and every documented transcript are untouched; no other
command changes. `report`'s lead time, phases and per-currency sums are
later tasks.
