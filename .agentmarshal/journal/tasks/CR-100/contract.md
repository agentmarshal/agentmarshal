+++
schema = 2
id = "CR-100"
title = "A leak-scan hit says where and what, without printing the secret; the reviewer's diagnostics survive; the outbox says it is not evidence"
scope = [
  "src/agentmarshal/journal/capture.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/cli.py",
  "src/agentmarshal/project.py",
  "tests/test_capture.py",
  "tests/test_gate.py",
  "tests/test_review_launcher.py",
  "tests/test_project.py",
  "tests/test_placement.py",
  "openspec/changes/adopter-small-defects/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
  "openspec/specs/reviewer-adapter/",
]
acceptance = [
  "every scenario in openspec/changes/adopter-small-defects/specs/ is demonstrated by a test whose docstring names it; the implementation follows design.md's decisions or records in design.md why it departed",
  "no output of the scan contains the matched text or a configured marker's value, and a test asserts a marker placed in the scanned content does not appear in the rendering",
  "the standalone command and the gate's added-content warning render the same hit records, so the two cannot drift; a test pins the gate's line",
  "a private-marker hit whose only occurrence is the configuration declaring the markers is not reported, and the same marker elsewhere in the same content still is",
  "a zero-exit reviewer command's error output is kept outside any journal with its path named, a command that wrote nothing there says nothing, and the byte-for-byte gate transcript tests and the pinned prompt test pass with their expectations unmodified",
]
decisions = ["ADR-0005", "ADR-0008"]
documents = ["openspec/changes/adopter-small-defects/", "openspec/specs/leak-scan/"]
+++

# CR-100: three small defects an adopter paid for

## Context

Three findings from the adopter batch, each cheap to fix and each costing its
reporter real work: a leak-scan refusal that named only a category, a marker
list that matched its own declaration, reviewer diagnostics discarded on
success, and an outbox that nothing says is not evidence (proposals 020, 021 and
023).

## Objective

A refused transaction tells the operator where to look. A wrapper that warns is
heard. An outbox that is not evidence says so.

## Threat model and boundaries

The scan exists to keep secrets out of a public repository, so its own output
must not carry one. A private marker is the secret: it is named by its position
in the operator's configuration, never by value. The built-in signatures are
public patterns, and naming one discloses nothing.

Dropping a self-match is a narrowing of the scan, and the narrowing is bounded
by location: only an occurrence inside the configuration that declares the
marker is ignored, and only when it is the sole occurrence.

## Amended 2026-09-17

`tests/test_placement.py` joins the scope. The standalone command's headline
changes in this task — it renders records now, not categories — and that file
asserts the old wording. The scope named the four test files the work was
expected to touch and missed the one an output change reaches.

## Non-Goals

- An acknowledged-and-proceed path for a verified false positive: proposal 020
  asks for one, it is a new record type, and this project decides record types
  in an ADR first.
- The `upstream` command proposal 023 proposes; the documentation sentence is
  what lands here.
- Any change to what the gate refuses: the added-content scan stays advisory.
