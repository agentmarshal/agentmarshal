## Context

The contract header's TOML front matter is parsed by `parse_contract_text`
in `src/agentmarshal/journal/contracts.py` before anything the contract
names is trusted. The header has a schema numbering of its own — a new field
arrives under the schema that introduces it
(ADR-0015): schema 2 added `decisions`, `documents` and `extensions`, each
optional, each refused in a schema-1 header with a message naming the field
and the schema it requires. ADR-0022 section 5 defines schema 3's three
fields; ADR-0018 decision 3 defines what they mean: the permitted
implementers and reviewers, each an ordered list of declared actors whose
order is the fallback order, and the independence rules in force from a
fixed vocabulary.

## Goals

- A schema-3 header parses `implementers`, `reviewers` and `independence`
  and the parsed `ContractHeader` exposes them.
- A malformed declaration is refused at the boundary with a message naming
  the field, in the style of the existing messages — which name the field
  and the source.
- The schema ladder holds: schema 4 is unknown, and the three new fields
  refuse under schema 1 and 2 exactly as the schema-2 fields refuse under
  schema 1.

## Non-Goals

- Any gate check of the fields: membership of implementers and reviewers,
  the independence rules, "not checked" when a field is missing. The gate
  reads the parsed header in later tasks.
- Validating actor ids against a project's actors table — a later task; an
  actor is a declared label until signing exists (ADR-0006).
- Writing schema-3 headers from `open` — a later task.
- A status line or doctor check of these fields.

## Decisions

- **The three fields share one helper.** `implementers`, `reviewers` and
  `independence` have the same shape — an optional, non-empty list of
  distinct non-empty strings — so one helper parses them and applies the
  shared refusals before `independence`'s vocabulary check runs against the
  already-validated entries.
- **An empty list is refused, not read as absent.** The absent field means
  "no assignment declared", and the gate will read it as unconstrained; an
  explicit `implementers = []` would more plausibly read as "no implementer
  permitted", which makes a task unworkable. Refusing resolves the ambiguity
  toward the mistake it almost certainly is.
- **A repeated entry is refused.** The order of the lists is the fallback
  order, so a list may not be normalised to a set — but a repeated entry
  adds nothing to an ordered list and is a mistake the writer should fix.
- **The independence vocabulary is checked at parse.** The gate can only
  check rules it knows, so a name outside the four is a typo, not a policy —
  the refusal names the rule it did not know.
- **Entries pass the record side's forgeable-text rule.** Actor ids and rule
  names render into briefs and status output like the schema-2 fields do, so
  each entry goes through `reject_control_characters` — the same predicate,
  so the two sides cannot drift.
- **Actor ids are not validated further.** Non-empty, distinct,
  control-character-free strings parse; whether a named actor exists is the
  project's actors table's question, asked by a later task — an actor id is
  a declared label, and this change only declares it.
