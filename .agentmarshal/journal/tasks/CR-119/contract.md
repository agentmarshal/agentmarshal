+++
schema = 1
id = "CR-119"
title = "Tails of 0.4.x: sidecar wording, line wraps, a stale test docstring, the outbox README points at the tracking section"
scope = [
  "docs/sidecar.md",
  "docs/quickstart.md",
  "docs/proposals/024-provider-quota-stop-cannot-be-recorded.md",
  "tests/test_gate.py",
  "src/agentmarshal/project.py",
  "tests/",
]
acceptance = [
  "docs/sidecar.md no longer presents the token record as what a task cost — its heading 'Complete, and record what it cost' and any sentence under it saying so use the wording the quickstart's step 7 uses — and its table of commands describes submit-review and accept accurately for this release, checked against the CLI's own options",
  "prose lines that CR-113 changed in docs/quickstart.md's step 7 and in docs/proposals/024-provider-quota-stop-cannot-be-recorded.md are wrapped to the width of the text around them; tables and code blocks are left as they are",
  "the docstring of released_030 in tests/test_gate.py no longer says that the version string cannot tell the released 0.3.0 from a build of this repository — since CR-112 a build reports a .dev0 version — and says what the finding-command probe still guards against; the test's logic is unchanged",
  "the outbox README that `agentmarshal init` writes tells the reader how to find what became of a finding they sent — hash the file and look for that hash in the Source line of the published digests — and a test asserts the generated README says so",
  "no statement names a release, task or document that is not published, and the full CI sequence passes",
]
+++

# CR-119: tails of 0.4.x

## Context

Small items left by tasks of the 0.4.x line, none of which changes behaviour
beyond one generated text.

- CR-113 stopped presenting token counts as what a task cost in the quickstart
  and README; `docs/sidecar.md` still has a heading "Complete, and record what
  it cost", outside that task's scope.
- CR-113's edits left some lines of step 7 and of proposal 024 unwrapped.
- `released_030` in the gate tests says the version string cannot tell the
  published 0.3.0 from a build of this repository. CR-112 made every build from
  the default branch report a `.dev0` version, so that sentence is no longer
  true, though the probe it explains still has a use.
- The proposals index has a section on matching a sent finding to its digest
  by sha256. An adopter who sent ten findings did not find it and asked; the
  outbox README that `init` writes is where they look, and it does not say.

## Objective

The documents and the generated outbox README say what the tool and the
project do now.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any other change to the outbox README, or to `init`'s other output.
- A command that reports the fate of sent findings (proposal 023's command).
- Rewrapping text CR-113 did not touch.
