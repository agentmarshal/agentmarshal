+++
schema = 2
id = "CR-195"
title = "One function builds the acknowledgement mark for leak-scan and the gate; the leak-scan specification says it is masked; two untested paths get tests"
scope = [
  "src/agentmarshal/journal/capture.py",
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/acknowledge.py",
  "tests/",
  "openspec/changes/acknowledgement-mark-one-place/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
]
acceptance = [
  "the change acknowledgement-mark-one-place has a proposal, a design.md and a delta spec on the capability leak-scan, MODIFYING the requirements CR-190 and CR-193 added so that they state the mark — who acknowledged and the reason — is masked by the leak scan and escaped on display; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "one function in src/agentmarshal/journal/capture.py builds the mark, and both `leak-scan` (cli.py) and the gate (gate.py) call it; the output of both is byte for byte what it is now, which existing tests demonstrate unchanged",
  "the design.md files of the archived changes of CR-190 and CR-193 no longer claim what is untrue (that the matched text cannot reach the mark; that the mark is already shared) — a dated correction line in each, the rest left as written",
  "src/agentmarshal/acknowledge.py's docstring no longer says acknowledgements are not honoured anywhere; a test reads acknowledgements in a sidecar placement (records in the journal repository, scan in the host), and a test pins that `leak-scan --help` lists `--task`",
  "no behaviour changes in any command; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/leak-scan/"]
decisions = ["ADR-0021"]
+++

# The acknowledgement mark in one place

## Context

Reviews of CR-190 and CR-193 left advisory findings, deferred to one task:
the mark an acknowledged hit carries is built twice (cli.py for
`leak-scan`, capture.py for the gate) though CR-193's design says it is
shared; the leak-scan specification promises only that the mark is escaped,
while the code also masks it and CR-190's design says the matched text
cannot reach it; `acknowledge.py`'s docstring still says acknowledgements
are not honoured; the sidecar read path and `leak-scan --help` listing
`--task` are untested. None changes behaviour; all keep the documents
true.

## Objective

The mark has one implementation and the documents describe it as it is.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change to what the scan matches, to the mark's content or to exit
  statuses.
- Rewriting the archived design documents beyond a dated correction.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
