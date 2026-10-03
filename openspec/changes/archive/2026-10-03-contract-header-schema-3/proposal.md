## Why

ADR-0018 decision 3 lets a contract name its permitted implementers and
reviewers, in fallback order, and the independence rules in force; ADR-0022
section 5 puts the three fields in contract header schema 3. Nothing parses
them yet — a header declaring `schema = 3` is refused as an unknown schema
version, so a contract cannot carry the assignment the gate will later check.

## What Changes

Contract header schema 3 exists. A schema-3 header may carry `implementers`
and `reviewers` — ordered lists of non-empty actor ids, the order kept — and
`independence` — a list drawn from exactly `reviewer-not-writer`,
`distinct-actor`, `distinct-vendor` and `distinct-model`. Each field is
optional. An empty list, a repeated entry, an entry that is empty or not a
string, or an entry carrying a character the record side refuses is refused
naming the field; an `independence` entry outside the vocabulary is refused
naming the rule. Any of the three fields in a header of schema 1 or 2 is
refused as requiring schema 3, as the schema-2 fields are refused in schema 1
today. Schema 4 remains an unknown schema, and headers of schema 1 and 2
parse exactly as before.

## Capabilities

- new: `contract-governance`

## Impact

Parsing and validation only: the parsed `ContractHeader` exposes the three
fields and nothing reads them yet. Checking them — membership, the
independence rules, "not checked" when a field is missing — belongs to the
gate in later tasks, as do validating actor ids against a project's actors
table and writing schema-3 headers from `open`.
