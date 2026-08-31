+++
schema = 1
id = "CR-063"
title = "Ask the reviewer to state each finding's claim in words"
scope = ["src/agentmarshal/journal/review.py", "tests/test_review_launcher.py", "docs/quickstart.md"]
acceptance = [
  "the review prompt asks for one line of prose per finding id, before the verdict block, naming what is wrong and where",
  "the prompt says the ids are labels and the prose is what a human will read",
  "the verdict protocol itself is unchanged: the same required and optional keys, refused the same way",
  "the quickstart states that the prompt asks for this, alongside its description of the protocol",
]
+++

# CR-063: Ask the reviewer to state each finding's claim in words

## Context

A review record carries finding **ids** and nothing else. CR-054 made the
launcher keep the reviewer's raw output whenever a recorded verdict names a
finding, so the reasoning survives — but only if the reviewer wrote any.

Three times in one session it did not. Verdicts arrived carrying
`advisory_findings: ["TEST-ENV-001"]`, `["API-001"]`,
`["tests-not-run-read-only-temp-environment"]` and an output file whose entire
contents were the verdict block. The preserved file is faithful and useless: it
keeps what was written, and nothing was written.

The prompt is why. It specifies the machine protocol precisely — the sentinels,
the keys, which may be empty — and never asks for a sentence. A reviewer that
emits ids and stops has followed the instructions exactly.

## Objective

Ask for the claim in words, so a preserved output says what a finding means.

## Acceptance Criteria

- The prompt asks for **one line of prose per finding id**, printed before the
  verdict block, naming what is wrong and where.
- It says plainly that the ids are labels for the machine and the prose is what
  a human will read.
- The verdict protocol is otherwise **unchanged**: the same required keys, the
  same optional `advisory_findings`, the same refusal of anything else.
- The quickstart says the prompt asks for this, where it describes the protocol.

## Threat model and boundaries

No adversary. This edits a prompt string built from the operator's own contract
and their own diff, and sends it to a reviewer the operator configured.

Not defects in this task, and not to be guarded against: prompt injection from
contract or diff content (both are the operator's own repository, and the
reviewer is read-only in a metadata-free snapshot by existing design); the
reviewer ignoring the request, which nothing can prevent and which the
acceptance criteria do not claim to.

## Non-Goals

- **Requiring the prose.** Nothing can enforce what a model writes, and a check
  that rejected a verdict for missing prose would throw away a valid verdict
  over its formatting. Ask, do not demand.
- Parsing the prose, extracting it into the record, or associating lines with
  ids programmatically. What is retained durably is the capture policy's
  question (ADR-0005), which is roadmap.
- Changing the verdict keys, the sentinels, or record validation.
- Changing what CR-054 preserves or where.
