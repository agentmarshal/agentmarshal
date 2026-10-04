+++
schema = 2
id = "CR-177"
title = "An agreement record of schema 7 records that a declared actor agrees with the contract at a stated hash"
scope = [
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/attestation.py",
  "src/agentmarshal/journal/status.py",
  "tests/",
  "openspec/changes/agreement-record/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change agreement-record has a proposal, a design.md and a delta spec adding to contract-governance the agreement record (ADDED requirements; MODIFIED with exact headers only where one becomes untrue); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "an `agreement` record type exists from schema 7, declared once in the record-type registry (predicate type, projected state, writable, not admitted after a terminal record, `recorded_by` with `recorded_by_source` required, as ADR-0022 section 3 lists it); its one own field is `contract` — the sha256 of the contract text agreed with, exactly 64 lowercase hex characters, the form `contract_sha256` produces and `opened`/`amendment` carry",
  "a recorder that is not a declared actor is accepted, as on the other schema-7 types that require `recorded_by`; an agreement record below schema 7 is refused at write and on read; writing one stamps 7; no other record type changes",
  "nothing reads agreements yet beyond what every record type gets: `validate` and `status` handle a task carrying one without failing, and the gate admits a candidate adding one exactly as it admits the other schema-7 types the projection admits before a terminal record",
  "the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
+++

# The agreement record

## Context

ADR-0018 decision 2: a record exists for agreement with the contract — a
declared actor states agreement with the contract at a stated hash. The
gate does not require it by default; `status` shows its absence and who
agreed; a project may require it (`contract.require_agreement`). Any
declared actor may record it — there are no roles. ADR-0022 section 3
gives it schema 7 with one field, `contract`, and requires `recorded_by`
with `recorded_by_source`. CR-171 pins the contract's hash on `opened` and
`amendment`; this record states agreement with one such hash. The `agree`
command, the gate's `require_agreement` check and `status` showing
agreement are later tasks.

## Objective

The journal can carry an actor's agreement with a contract at a hash.

## Acceptance Criteria

As in the header.

## Non-Goals

- The `agree` command, comparing the agreed hash with the contract's
  current or pinned hash, the gate's `require_agreement` check, and how
  `status` shows agreement or its absence (later tasks).
- Roles or any restriction on who may agree (ADR-0018 decision 2).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
