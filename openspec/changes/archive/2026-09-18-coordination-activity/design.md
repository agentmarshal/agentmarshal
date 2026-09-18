## Context

`records.py` validates `activity in _SESSION_ACTIVITIES` with
`{"implementation", "review", "other"}`; `backfill.py` keeps its own copy of
the same set and normalizes unknown values to `other`. The CLI help spells the
three values out. Supported schemas are 1–5; ADR-0004 fixes the floor rule — a
writer stamps a higher schema only when the record uses what that schema
introduced (`_SCHEMA_5_FIELDS` is the precedent for a field).

## Goals

- `coordination` is a valid activity everywhere a session record is written or
  read.
- One vocabulary.
- An older reader's refusal of a coordination record is legible.

## Non-Goals

- A money field. Deferred by the disposition of proposal 018, for the reason
  given there.
- A per-activity breakdown in `report`.
- Rewriting existing records.

## Decisions

- **A new value is a schema change, and gets a schema number.** The floor rule
  was written for fields, but a reader that predates `coordination` refuses the
  record either way — the question is only whether it says "unsupported schema
  6" or "unsupported activity". The first is the refusal the schema mechanism
  exists to give, and it matches the ADR-0004 rule's intent: records carry the
  number of the change whose vocabulary they use. Only records that use the
  value carry it, so no journal gets the newer number without needing it.
- **`backfill.py` reads the vocabulary from `records.py`.** Its copy is the same
  set today and would silently normalize a coordination session to `other` the
  day the two differ.

## Risks

- [A journal with a coordination record is unreadable by 0.3.0] → true, and
  stated in UPGRADING at release. The refusal is about the schema, but it does
  not name the number: 0.3.0 says "record has an unknown or missing schema
  version". That is still the better of the two refusals an older reader could
  give — it points at versions, not at a field value — and UPGRADING has to
  carry the specific "a coordination session needs 0.4.0" itself.
