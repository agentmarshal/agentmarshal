+++
schema = 2
id = "CR-214"
title = "validate warns when an ext record's kind is declared by no shared extension's manifest, without refusing the journal"
scope = [
  "src/agentmarshal/journal/validate.py",
  "tests/",
  "openspec/changes/validate-addressee-not-found/",
  "openspec/changes/archive/",
  "openspec/specs/extension-records/",
]
acceptance = [
  "the change validate-addressee-not-found has a proposal, a design.md and a delta spec on the capability extension-records with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal validate` reads the `[records].kinds` declared by the manifests of shared extensions in the working tree — file and directory form — and prints one WARN line per `ext` record whose `kind` no manifest declares, naming the task, the record id and the kind as \"addressee not found\" (ADR-0013 decision 18); the warning does not change validate's exit status or its passed/failed verdict",
  "a manifest that cannot be read is named on one WARN line and its kinds count as undeclared; a journal with no `ext` records reads no manifests and prints exactly what validate prints today, which a test pins byte for byte",
  "every value from a record or a manifest is escaped on display as validate's other lines are; the gate does not read the warning and no other command changes",
  "the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-records/"]
decisions = ["ADR-0010", "ADR-0013"]
+++

# validate: addressee not found

## Context

ADR-0013 decision 18: `validate` checks the `ext` envelope; a kind no
manifest declares draws a warning — "addressee not found", not a refusal —
because a record can outlive the manifest that declared its kind. Reading
the declared kinds makes `validate` another reader of manifests, after
`brief`, the gate and `doctor`. CR-179 landed the record, CR-212 the
command that writes it only for a declared kind, CR-152 the `[records].kinds`
declaration.

## Objective

A reader of `validate` sees an `ext` record whose extension no longer
declares it, without the journal failing.

## Acceptance Criteria

As in the header.

## Non-Goals

- Refusing a record over its kind.
- Reading the payload.
- Personal or user-scope manifests (they write no records).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
