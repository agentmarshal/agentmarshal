+++
schema = 2
id = "CR-107"
title = "Documentation debts before 0.4.0"
scope = [
  "docs/",
  ".github/workflows/agentmarshal-governance.yml",
  "openspec/changes/archive/",
  "tests/test_placement.py",
]
acceptance = [
  "this repository's own .github/workflows/agentmarshal-governance.yml runs the gate the way the shipped template does — with --without-review, without continue-on-error, and with a comment that says it is the required check and not the merge authority; the two gate jobs differ only where this repository's setup genuinely differs, and each difference is commented",
  "the archived design.md of the adopter-small-defects change no longer points the reader at a record they cannot see, and no document under docs/ or openspec/changes/archive/ does — checked by a grep whose command and result are quoted in the commit message",
  "the archived proposal.md and design.md of the writer-refuses-a-closed-task change state the prior state as the task's merge diff shows it: which writers had their own refusal, how many, whether reopen had its own check, whether the launcher's pre-run refusal was new for each binding, and how many call sites in how many modules — each number taken by a command over that diff and quoted in the commit message",
  "ADR-0009 and ADR-0010 each gain a short example section pointing at a working artefact in this repository, marked as non-normative",
  "the sidecar branch of `complete` refusing a closed task is pinned by a test in tests/test_placement.py",
]
decisions = ["ADR-0009", "ADR-0010"]
+++

# CR-107: documentation debts before 0.4.0

## Context

Step 13 of the plan, plus what today's tasks left behind. Each item is a place
where a published document says something the code or the history does not:

- This repository's own workflow still carries the arrangement CR-099 retired —
  `continue-on-error`, no `--without-review`, "advisory until Phase C" — so we
  ship one arrangement and live by another.
- CR-100's archived design.md says a deferred decision "is recorded as its own
  backlog item"; the register it means is not published.
- CR-102's archived proposal.md and design.md misstate the prior state in four
  places, two of them introduced by corrections made during review.
- ADR-0009 and ADR-0010 have no worked example; this repository has one of
  each (the findings-lane runbook, the OpenSpec manifest).
- The sidecar branch of `complete` gained a guard in CR-102 that no test pins.

## Objective

The published documents say what the code and the history say.

## Acceptance Criteria

See the `acceptance` field above.

## Non-Goals

- Transcripts captured from a release build: they need the release build, and
  belong to the release task.
- Rewording documents that are accurate. This is a correction pass, not an
  edit pass.
- Any behaviour change except the one this repository's CI gains by running
  its own gate as the template does.
