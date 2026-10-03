+++
schema = 2
id = "CR-163"
title = "One function hashes a contract's text, and opened and amendment records of schema 7 may carry that hash"
scope = [
  "src/agentmarshal/journal/contracts.py",
  "src/agentmarshal/journal/records.py",
  "src/agentmarshal/journal/review.py",
  "tests/",
  "openspec/changes/contract-hash/",
  "openspec/changes/archive/",
  "openspec/specs/contract-governance/",
]
acceptance = [
  "the change contract-hash has a proposal, a design.md and a delta spec modifying the contract-governance capability (ADDED requirements for the hash and the field; MODIFIED with exact headers only if an existing requirement becomes untrue); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`contract_sha256` in contracts.py takes a contract's bytes as stored or read, decodes them as UTF-8, translates CRLF and lone CR to LF as Python's text reading does, and returns the lowercase hex sha256 of the result encoded as UTF-8; a contract checked out with CRLF line endings hashes to the same value as the same contract with LF; a byte-order mark is kept as text reading keeps it; undecodable bytes are refused with a message naming the source",
  "the review launcher computes `reviewed_contract` with this function; for every contract the launcher reads today the value is unchanged (a test computes it both ways on LF, CRLF and BOM-bearing inputs), so review-evidence's requirement stays true",
  "`opened` and `amendment` records may carry `contract` (64 lowercase hex) from schema 7 only, registered through the record-type registry and field families like the session fields of CR-160; a record carrying it stamps 7, one without it stamps what it stamps today; below 7 it is refused at write and on read by the field-admission rule",
  "no writer sets the field yet (`open`, `amend` and `migrate` are a later task), the gate's fixtures are unchanged, and the full CI sequence passes",
]
documents = ["openspec/specs/contract-governance/"]
+++

# CR-163: the contract hash

## Context

ADR-0018 decision 1: the `opened` record and every `amendment` carry the
sha256 of the contract text they establish, in the lowercase hex
`reviewed_contract` already uses. ADR-0022 puts the field in schema 7.
Today the review launcher hashes text read with newline translation, while
the gate reads raw `git show` output — the same contract could hash two
ways on a checkout with CRLF line endings. One function must serve every
place that hashes a contract. Writing the field from `open`, `amend` and
`migrate` is the transition itself, a later task.

## Objective

There is one way to hash a contract, and the records that establish a
contract can carry its hash.

## Acceptance Criteria

As in the header.

## Non-Goals

- Writing the field from `open`, `amend` or `migrate` (the transition task).
- Any gate or status reading of the field.
- Recomputing hashes in existing records.
