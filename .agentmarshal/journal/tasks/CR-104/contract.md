+++
schema = 2
id = "CR-104"
title = "The launcher's two paths share one tail, and the identity rule lives with the actors"
scope = [
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/actors.py",
  "tests/test_review_launcher.py",
  "tests/test_gate.py",
  "tests/test_findings.py",
]
acceptance = [
  "the commit path and the finding path of the review launcher run the reviewer, parse the verdict, record the review and build the result through one shared function; neither path keeps its own copy of that sequence",
  "the recorder-identity resolution and the independence refusal live in actors.py and are read from there by both the gate and the launcher; gate.py keeps no copy and the launcher no longer imports the gate for them",
  "no behaviour changes: every existing test passes with its expectations unmodified, including the byte-for-byte gate transcript tests and both pinned prompt tests",
  "the gate's findings-lane transcript line about reviewer independence is byte-identical to what it was",
]
decisions = ["ADR-0006", "ADR-0009"]
+++

# CR-104: one tail for the launcher, one home for the identity rule

## Context

CR-101 gave the review launcher a second path, for a finding, and wrote it as a
parallel copy of the commit path. Review found the duplication three times: the
verdict parser and the prompt scaffolding were merged during that task; the
tail — temporary directory, prompt file, reviewer run, diagnostics, decode,
parse, submit, the artifact-reference branch, the result — was left as two
copies, and both deciding runs named it in two consecutive rounds.

Beside it, the identity rule the findings lane applies (ADR-0006, ADR-0009
Decision 3) lives in `gate.py`, so the launcher imports the merge gate — its
leak scan, capture and git machinery — to ask whether a reviewer is independent
of a finding's recorder. `actors.py` owns ADR-0006 and already exports the
source constants that resolver uses.

## Objective

Each rule and each sequence exists once, in the module that owns it.

## Acceptance Criteria

See the `acceptance` field above.

## Non-Goals

- Any change in behaviour. This task carries no delta spec by the criterion the
  project uses: nothing it does can be named as "when X, the system does Y"
  that was not already true.
- The gate's encoding of what a closed task admits: a separate task, because
  it is a behaviour defect rather than a placement.
- Changing a refusal's wording.
