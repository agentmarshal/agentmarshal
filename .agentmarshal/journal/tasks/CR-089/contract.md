+++
schema = 1
id = "CR-089"
title = "The gate reads manifests: effective scope, the named-documents line, the removal check"
scope = [
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/contracts.py",
  "src/agentmarshal/journal/extensions.py",
  "src/agentmarshal/journal/brief.py",
  "src/agentmarshal/journal/review.py",
  "src/agentmarshal/journal/open_task.py",
  "tests/test_gate.py",
  "tests/test_placement.py",
  "tests/test_findings.py",
  "tests/test_extensions.py",
  "tests/test_brief.py",
  "tests/test_journal.py",
  "tests/test_review_launcher.py",
  "docs/overview.md",
  "docs/quickstart.md",
  "docs/sidecar.md",
]
acceptance = [
  "the scope matcher has one public home in contracts.py and gate.py, extensions.py and brief.py use it; the private name in gate.py is gone",
  "for a task whose base-side contract names extensions, the gate's effective scope is the contract's scope plus the footprint of each named extension's manifest, read where the contract is read (the merge-base tree; in a sidecar, the sidecar working tree); the scope line names the extensions that contributed; a named manifest absent or malformed on that side is a refusal naming the extension and the reason",
  "a candidate that changes a path under a manifest's footprint under a contract that neither names the extension nor lists the path is refused with the existing paths-outside-contract-scope line",
  "when the base-side contract names documents — its own and each named extension's — the diff lane prints one line: PASS naming the touched paths when the candidate's diff adds, modifies or deletes at least one path under any named entry, FAIL naming the untouched entries otherwise; the journal-only lane prints nothing about documents; the findings lane prints a NOT EXAMINED line with its reason",
  "'under a documents entry' is defined once for brief and gate as the scope matcher applied to lexical paths: the gate compares diff paths, the brief lists files by lexical path under the entry and does not follow a linked subdirectory out of it; the brief test that walked a linked subdirectory is changed to that rule",
  "a candidate that deletes a manifest present on the base side is a removal: the diff lane prints a PASS line when no path of that manifest's footprint remains in the candidate tree and a FAIL line naming the remaining paths otherwise; a candidate that edits footprint paths and keeps the manifest gets no such line",
  "a symlink loop met while resolving a document path or a manifest path is reported — unresolvable in the brief, a refusal from the manifest reader — and raises nothing",
  "the diff-lane transcript of a task whose contract names neither extensions nor documents is unchanged: the existing byte-for-byte test against the released 0.3.0 and the sidecar transcript tests pass with their expectations unmodified",
  "in a sidecar the manifest is read from the sidecar working tree, its footprint names host paths, and the scope, documents and removal lines are advisory as every sidecar check is — demonstrated by a host-plus-sidecar test",
  "scope_warnings' docstring lists the docs/adr/ warning and the quickstart's list of open warnings names it; overview and sidecar.md describe the new gate lines in a sentence each; the reviewer prompt's fixed text is one module constant with no sentence split across literals, and the golden prompt test passes unchanged",
]
+++

# CR-089: the gate reads manifests

## Context

CR-088 built the reading side of ADR-0010: a contract names decisions,
documents and extensions; a manifest is read and validated; the brief and the
review prompt carry the named material. Nothing yet decides. This task adds
the three gate behaviours ADR-0010 D2, D3 and D5 decide — effective scope from
a footprint, the named-documents line, the removal check — and fixes the edges
the CR-088 reviews left for it: one public matcher, one meaning of "under a
documents entry", symlink loops reported rather than raised.

## Objective

Make the gate enforce what a contract and a manifest declare, reading both
from the side the candidate cannot edit, and leave every transcript that names
neither extensions nor documents exactly as 0.3.0 printed it.

## Acceptance Criteria

As in the header, with these clarifications:

- Reading side (ADR-0010 D2): the gate reads a manifest where it reads the
  contract — `git show <merge-base>:.agentmarshal/extensions/<name>.toml` in
  the embedded placement, the sidecar working tree in a sidecar. `brief` and
  the review prompt keep reading the working tree and the reviewed snapshot:
  they are context; only the gate decides. Which reader trusts which side is
  stated in one docstring in extensions.py.
- The removal check reads the manifest from the base side and lists footprint
  paths present in the candidate tree (`git ls-tree`), not the working tree.
- Transcript parity holds by construction: every new line is emitted only
  when the base-side contract names an extension or a document, or the
  candidate deletes a base-side manifest.
- "Advisory as every sidecar check is": the lines print in the sidecar
  transcript under the advisory notice, as the scope line already does.

## Threat model and boundaries

A candidate that ships a manifest edit cannot widen its own effective scope
or silence the documents line: both are read from the base side. A candidate
that deletes a manifest is held to the base-side footprint it can no longer
edit. The gate executes nothing from a manifest.

The one enforcement this adds — named documents must be touched — checks that
a change happened, not that it is true; the transcript wording says "touched".

## Non-Goals

- `extension add` / `extension remove` commands, templates, or executing a
  manifest's `install`/`remove` strings.
- Any automatic pinning of `artifacts` at completion: ADR-0010 D5 gives
  archival to an operator-recorded finding, and this task leaves it there.
- A size cap for documents in the brief.
- Changing the findings lane beyond its one NOT EXAMINED line.
