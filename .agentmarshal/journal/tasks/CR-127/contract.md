+++
schema = 2
id = "CR-127"
title = "One undecodable file no longer switches the leak scan off: the scan works per file and names what it could not read"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/capture.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/per-file-leak-scan/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
]
acceptance = [
  "every scenario in the change's delta spec is demonstrated by a test whose docstring names it, and the implementation follows design.md's decisions or records in design.md why it departed; the change is archived with the archive command into openspec/specs/leak-scan/",
  "the reproduction published in proposal 026's fourth finding is a test for both the gate's scan and the leak-scan command: a commit adding a text file holding a secret-shaped string and a file of bytes that are not UTF-8 reports the string — one file that does not decode no longer leaves every other file unscanned",
  "a file whose added content does not decode is named in the output of both the gate and the command, never passed over in silence; whether its bytes are still searched for what can be found in them, and what the command's exit status is when such a file is the only thing to report, is decided in design.md and stated in the delta spec",
  "the scan's existing guarantees still hold, each still pinned by a test: no matched text, no private marker's value and no path carrying a secret is printed; a path whose bytes are not UTF-8 is named in an escaped printable form; the gate's scan stays advisory and the command never ends in a traceback",
  "the full CI sequence passes",
]
documents = ["openspec/specs/leak-scan/"]
+++

# CR-127: the leak scan works per file

## Context

Proposal 026's fourth finding (one adopter) and proposal 037 (another) share a
root cause: git's diff output is decoded as UTF-8 strictly and as a whole. In
the gate, one undecodable byte raises and the scan degrades to "WARN:
leak-scan skipped" for the entire diff; the `leak-scan` command refuses the
same way. Upstream reproduced it on 2026-10-01: a commit with a
secret-shaped string in a text file and a file of random bytes reported
nothing; without the binary file it reported the string. The published
disposition: a file that does not decode should cost its own readability,
not every file's scan.

`review` has the same strict decode and fails with a traceback; that is a
separate task, which can reuse what this one builds.

## Objective

The leak scan reads git's diff per file, scans everything it can, and names
what it could not.

## Acceptance Criteria

As in the header.

## Non-Goals

- `review`'s diff handling (separate task).
- A diff-size limit (deferred).
- Changing the built-in signatures or the marker configuration.
