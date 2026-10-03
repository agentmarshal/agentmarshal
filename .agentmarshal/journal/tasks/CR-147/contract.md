+++
schema = 2
id = "CR-147"
title = "Contract header schema 3: who may implement, who may review, and the independence rules in force"
scope = [
  "src/agentmarshal/journal/contracts.py",
  "tests/",
  "openspec/changes/contract-header-schema-3/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change contract-header-schema-3 has a proposal, a design.md and a delta spec adding the contract-governance capability; every scenario in the delta spec is demonstrated by a test whose docstring names it; the change is archived with the archive command into openspec/specs/contract-governance/",
  "a schema-3 contract header parses `implementers` and `reviewers` as ordered lists of non-empty actor ids, keeping their order, and `independence` as a list drawn from exactly reviewer-not-writer, distinct-actor, distinct-vendor and distinct-model; each is optional, an empty list or a repeated entry is refused with a message naming the field, an unknown independence rule is refused naming the rule, and every entry passes the same control-character rule the schema-2 string fields pass; the parsed header exposes the three fields",
  "any of the three fields in a header of schema 1 or 2 is refused with a message that the field requires schema 3, as schema-2 fields are refused in schema 1 today; a schema-3 header may carry the schema-2 fields",
  "schema 4 is an unknown contract header schema and is refused (the existing test that uses schema 3 as the unknown example moves to 4); headers of schema 1 and 2 parse exactly as before",
  "the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
+++

# CR-147: contract header schema 3

## Context

ADR-0018 decision 3 lets a contract name its permitted implementers and
reviewers, in fallback order, and the independence rules in force;
ADR-0022 section 5 puts them in contract header schema 3. This task parses
them. Checking them — membership, the rules, "not checked" when a field is
missing — is the gate's, in later tasks.

## Objective

A schema-3 contract header carries the assignment and the rules, parsed and
validated.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any gate check, status line or doctor check of these fields.
- Validating actor ids against the project's actors table (a later task).
- Writing schema-3 headers from `open` (a later task).
