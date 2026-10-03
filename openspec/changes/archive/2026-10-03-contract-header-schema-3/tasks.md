## 1. The parser

- [x] 1.1 `ContractHeader` exposes `implementers`, `reviewers` and
  `independence`, each a tuple of strings defaulting to empty — verify: the
  dataclass, and a schema-3 parse test.
- [x] 1.2 The schema check admits 3; schema 4 is refused as an unknown
  schema version, and the existing unknown-schema test example moves from 3
  to 4 — verify: the parametrized header test.
- [x] 1.3 Any of the three fields under schema 1 or 2 is refused with a
  message that it requires schema 3, as the schema-2 fields are refused in
  schema 1 — verify: a test parametrized over field and schema.
- [x] 1.4 Each field parses as an ordered list of non-empty strings, order
  kept, optional; an empty list, a repeated entry, an empty or non-string
  entry and an entry carrying control characters are each refused naming
  the field — verify: one test per refusal, a parse test for order and
  optionality.
- [x] 1.5 `independence` entries are drawn from exactly
  `reviewer-not-writer`, `distinct-actor`, `distinct-vendor`,
  `distinct-model`; an unknown rule is refused naming the rule — verify:
  test.
- [x] 1.6 A schema-3 header may carry the schema-2 fields — verify: test.

## 2. The change itself

- [x] 2.1 proposal.md, design.md, tasks.md and the contract-governance
  delta spec are written — verify: openspec validate.
- [x] 2.2 Every scenario in the delta spec is demonstrated by a test whose
  docstring names it — verify: grep the test docstrings against the spec's
  scenario headings.
- [x] 2.3 The change is archived with the archive command — verify:
  `openspec/specs/contract-governance/spec.md` exists and the change lives
  under `openspec/changes/archive/`.
