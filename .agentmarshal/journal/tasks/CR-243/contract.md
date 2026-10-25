+++
schema = 2
id = "CR-243"
title = "Release documentation states what the code does: the write-failure promise is narrowed to what holds, README names review-prose capture as shipped, and each proposal's Where summary matches the current index"
scope = [
  "CHANGELOG.md",
  "README.md",
  "docs/proposals/",
]
acceptance = [
  "CHANGELOG.md's 0.6.0 entry for the write-time fix (CR-236) promises only what holds: an encoding or serialisation failure before the file is created leaves no record file; it does not claim that any failed write leaves no partial record (a failure while writing or closing after creation is not rolled back — src/agentmarshal/journal/records.py write_record) (release-audit finding AUD-docs-claims-1-1)",
  "README.md no longer says the supplementary-artifact capture policy is inactive: review-prose capture is implemented (review.py, submit_review.py; levels commit/hash/off) and is named as such, while the capture classes and attestation projection that are not shipped are named separately as not shipped (AUD-docs-claims-1-2)",
  "every proposal body under docs/proposals/ whose current-status line (its Where or Disposition summary) says pending, not yet shipped or undecided for something that has shipped is updated to the status docs/proposals/README.md gives, keeping the distinction between the shipped part and work genuinely deferred — at least 012, 024, 025, 026, 027, 028, 029, 030, 031, 032, 034, 036, 037, 039, 040, 041, 042, 044 and 045, each checked against the code (AUD-docs-claims-1-3); a proposal's original finding text is not rewritten",
  "no other file changes; every link resolves; the suite and the full CI sequence pass",
]
documents = ["CHANGELOG.md", "README.md", "docs/proposals/"]
decisions = ["ADR-0009"]
+++

# Documentation claims, part 1

## Context

Release audit 0.6.0, docs-claims part 1 (gpt-6-astra, freeze commit
dff244b): three blocking statements in the release documentation — the
CHANGELOG over-promises the write fix, README calls an implemented capture
policy inactive, and many proposal bodies still describe shipped features
as pending although the index is current.

## Objective

A reader of CHANGELOG, README or a proposal learns what the code does now.

## Acceptance Criteria

As in the header.

## Non-Goals

- docs/ outside proposals (docs-claims part 2 covers it).
- Rewriting the findings proposals report.
