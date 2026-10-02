# ADR-0015: A rule applies from the schema that introduced it

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0004](ADR-0004-journal-data-model.md) (records are append-only;
a record declares its schema from day one; a writer stamps the minimum schema
a record needs), [ADR-0011](ADR-0011-contract-amendment-visibility.md) (the
same rule for `reviewed_contract`) and
[ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md) (the extension
manifest's schema). **It partly revises the
[record-text-safety](../../openspec/specs/record-text-safety/spec.md)
specification**: refusal at the boundary only becomes refusal at write time
and escaping on display. It answers
[proposal 025](../proposals/025-validate-refused-records-an-earlier-release-wrote.md)'s
second suggestion.

This ADR records a decision. The read-time rule table, the escaping and the
specification change it describes are **not implemented by this document**;
they follow in their own tasks. The present tense below is how a decision is
written, not a claim about shipped behaviour.

## Context

0.4.0 tightened the forgeable-text rule and came to refuse records that 0.1.0
had written lawfully — a narrow no-break space inside finding ids
([proposal 025](../proposals/025-validate-refused-records-an-earlier-release-wrote.md)).
The tasks those records belong to are closed and the journal is append-only,
so they cannot be repaired; the upgrade was halted and the pinned installation
stayed on 0.3.0. 0.4.1 narrowed the rule, but the cause remained: the next
tightening would repeat the story.

How it works today:

- every record carries `schema`; it carries `tool_version` too (`records.py`),
  but that field decides no rules;
- **a writer stamps the minimum schema the record needs**
  ([ADR-0004](ADR-0004-journal-data-model.md),
  [ADR-0011](ADR-0011-contract-amendment-visibility.md)): a new field or value
  carries the schema that introduced it — a review carrying
  `reviewed_contract` stamps 5, a `coordination` session stamps its own — and
  everything else stamps 3. That is how a pinned installation of the previous
  version keeps reading a journal a newer one writes to;
- a reader checks records strictly
  ([ADR-0004](ADR-0004-journal-data-model.md) D4) and refuses an invalid one;
- a new check over an **existing** field applies to every schema at once —
  that is how the story in proposal 025 happened;
- the contract header and the extension manifest carry schema numbers of
  their own.

## Decision

1. **Two sides to a check.**
   - **At write time** the writer checks input by the **current** rules —
     always, whatever minimum schema it stamps. Refusal is in place here:
     the author can still fix the input.
   - **At read time** a record is checked by the rules of **its own
     schema**. A later rule, bound to a later schema, does not apply to it.
2. **The minimum schema stays**
   ([ADR-0004](ADR-0004-journal-data-model.md)): a writer does not raise the
   number without a new field. A new rule over an existing field applies at
   write time immediately, and at read time only to records of the schema
   that introduced it, and above.
3. **Tightening at read time takes a new schema.** A loosening — as 0.4.1's
   was — applies to every schema at once: it breaks no history.
4. **Nothing refuses an existing record under a later rule.** Under its own
   schema's rules it is checked strictly, as now. There is no rewriting and
   no exception list (declined in
   [proposal 025](../proposals/025-validate-refused-records-an-earlier-release-wrote.md)).
5. **Rules that guard output apply by escaping on display** (the revision of
   the
   [record-text-safety](../../openspec/specs/record-text-safety/spec.md)
   specification). A newline in a record field would print a line the tool
   never said (`gate: passed`); a direction-control character would reorder
   what is seen. For records such a rule does not reach at read time,
   `status`, the gate's output, `report`, the brief and the reviewer prompt
   escape those characters (`\n`, `\u202e`). That also covers a record
   written around the writer with a lowered schema: it cannot forge output.
6. **Existing checks apply from schema 1**: since 0.4.1 every known journal
   satisfies them, and each cannot be bound to the schema of its own time —
   0.4.x writers stamped the minimum schema, so the rule would fall off the
   very records written under it.
7. **A table "rule → the schema it applies from at read time"** lives in
   record validation; a rule cannot be added without its number — a test
   catches that.
8. **The same for the contract header and the extension manifest**: each has
   its own numbering, and the rule is the same — checked by the current rules
   at write time, by its own schema's at read time. The schema of the `ext`
   envelope
   ([ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)) is
   settled by the later decision on the record model, under this rule.
9. **The record model that introduces new fields** — a later decision —
   brings its new fields and checks in under a single record schema (7), for
   the records that carry those fields.

## Consequences

- Upgrading the tool no longer makes an adopter's history invalid.
- New records are always checked by the current rules — at write time.
- A previous version's reader still reads new records that carry no new
  fields.
- Old records' output is escaped; the
  [record-text-safety](../../openspec/specs/record-text-safety/spec.md)
  specification changes from "refusal only" to "refusal at write, escaping
  on display".

## Alternatives considered

- **A writer always stamps the current schema** — pinned installations of
  the previous version would refuse every new record.
- **Rules by `tool_version`** — versions are many, and forks have their own.
- **An exception list** — declined in
  [proposal 025](../proposals/025-validate-refused-records-an-earlier-release-wrote.md).
- **Rewriting old records** — the journal is append-only.
