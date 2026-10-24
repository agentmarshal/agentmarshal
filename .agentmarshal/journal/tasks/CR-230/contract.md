+++
schema = 2
id = "CR-230"
title = "Digests 044 and 045 of Adopter A's findings: unmeasured usage written as zeros, and an outbox that predates outbox check"
scope = [
  "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md",
  "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md",
  "docs/proposals/README.md",
]
acceptance = [
  "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md digests Adopter A's finding with Source `sha256:816c7ff8e0ad09bd1bc55f0030897758eba0a539c0da556744de745a76e57b0d`, observed on 0.4.1 and rechecked on 0.5.0, in the form of the existing digests (reporter line, Finding, Disposition); the disposition is accepted: the reading side — status and report show such a session as unmeasured — in 0.6.0, and the write side — optional token counts with an explicit unmeasured marker — with the next record schema in 0.7.0",
  "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md digests Adopter A's finding with Source `sha256:a819341cbe9022523a08b200c6ee92e687335c6b83fd4b12a88b22b35a411008`, observed on 0.5.0; the disposition is accepted: `outbox check` and `outbox send` skip files already sent (by a sent manifest the send writes, or by the index `outbox status` takes) in 0.6.0",
  "docs/proposals/README.md lists both digests in its index in the existing row format",
  "no identifier of the adopter's repository appears in either digest — no task numbers, no record ids (ULIDs), no file or path names of its journal or scripts, no names of its people, provider account or product — only 'Adopter A' and facts about AgentMarshal; English only; every link added resolves",
  "no other file changes; the suite and the full CI sequence pass",
]
documents = ["docs/proposals/README.md"]
decisions = ["ADR-0009", "ADR-0020"]
+++

# Digests 044 and 045

## Context

Adopter A sent two findings on 2026-10-24 (staged privately). The intake
rule: public artifacts are English digests that name the adopter only by
its letter; the hash on the `Source:` line links each digest to the
original. A digest once published cannot be withdrawn, so the contract
forbids every adopter identifier, not only task numbers (a record id once
leaked into public history this way).

## Objective

Both findings are on the public index with their dispositions.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing either finding (separate tasks).
- Copying the originals.
