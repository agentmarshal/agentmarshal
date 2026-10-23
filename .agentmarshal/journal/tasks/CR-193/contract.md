+++
schema = 2
id = "CR-193"
title = "The gate marks an acknowledged leak-scan hit on its advisory line — who and why — within the line's existing bound"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/capture.py",
  "tests/",
  "openspec/changes/gate-marks-acknowledged-hits/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
]
acceptance = [
  "the change gate-marks-acknowledged-hits has a proposal, a design.md and a delta spec on the capability leak-scan with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "the gate's advisory leak-scan line marks each hit it shows that an `acknowledgement` record of the task acknowledges — same candidate commit, same file as the scan prints it, same identification (ADR-0021 decision 2) — with who acknowledged it and the reason, the same mark `leak-scan` prints since CR-190, masked and escaped as there",
  "the line's bound is unchanged: at most twenty hits shown, then \"and N more not shown\"; an acknowledgement neither removes a hit from the line nor changes which hits are shown or their order (ADR-0021 decision 3); the line stays a warning and blocks nothing",
  "a candidate whose task holds no acknowledgement for its commit produces today's line byte for byte — the pinned default transcript and the fixtures under tests/fixtures/ are unchanged; acknowledgements of another commit mark nothing",
  "no other gate check changes; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/leak-scan/"]
decisions = ["ADR-0021", "ADR-0022"]
+++

# The gate marks acknowledged hits

## Context

ADR-0021 decision 3: the gate, the command and `status` are the surfaces an
acknowledgement prints on; the gate prints the mark on the hits its line
shows, within the bound that line already has — at most twenty, then "and N
more not shown" — and an acknowledgement neither widens nor narrows that
bound. The gate's leak scan decides nothing; it warns. CR-187 landed the
`acknowledge` command, CR-190 the mark in `leak-scan`'s own output.

## Objective

A reader of the gate's transcript sees which reported hits someone has
already looked at, and who.

## Acceptance Criteria

As in the header.

## Non-Goals

- Turning the warning into anything that blocks.
- Self-acknowledgement marking on the gate's line (`status` carries it).
- Any change to the scan or to `leak-scan`.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
