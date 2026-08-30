+++
schema = 1
id = "CR-055"
title = "Document that a named finding keeps the reviewer's output"
scope = ["docs/quickstart.md"]
acceptance = [
  "the reviewer-protocol section states that a recorded verdict naming a finding keeps the reviewer's raw output and names the file on stderr",
  "it says the record path remains the only stdout line",
  "it says preservation is best effort and never costs the record",
  "the existing sentence about a refused verdict remains, since that behaviour is unchanged",
]
+++

# CR-055: Document that a named finding keeps the reviewer's output

## Context

The quickstart tells the reader that a **refused** verdict keeps the reviewer's
raw output — "a rejected verdict should not cost you the analysis". CR-054
extended that to a verdict that is *accepted* and names a finding, which is the
ordinary case. The published documentation is now true but incomplete: a reader
following it would not know the file exists, or where to look for it.

## Objective

Say what the tool now does, in the section where a reader is already learning
the verdict protocol.

## Acceptance Criteria

- The verdict-protocol section states that when a recorded verdict names a
  finding — blocking, or advisory alongside an approval — the reviewer's raw
  output is kept and `agentmarshal review` names the file on stderr.
- It states that the record path stays the only line on stdout.
- It states that preservation is best effort: a review is recorded even when
  the output cannot be kept.
- The existing sentence about a refused verdict stays; that behaviour did not
  change.

## Non-Goals

- Describing a capture policy for retaining reviewer prose durably (ADR-0005,
  roadmap). This documents a local file, not a retention scheme.
- Editing any other document.
