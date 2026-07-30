+++
schema = 1
id = "CR-041"
title = "advisory leak-scan-at-merge (provider-neutral)"
scope = ["src/agentmarshal/journal/capture.py", "src/agentmarshal/cli.py", "src/agentmarshal/journal/gate.py", "docs/adr/ADR-0005-evidence-capture-and-format.md", "tests/test_capture.py", "tests/test_gate.py", "tests/test_leak_scan.py"]
acceptance = [
  "a provider-neutral 'agentmarshal leak-scan --base <ref> --commit <ref>' command scans the ADDED content of the candidate diff, prints found categories (never the matched secret), exits 1 on any finding and 0 when clean",
  "capture.py gains scan_diff_for_leaks() reusing scan_for_leaks(); private markers are read from an optional project.json 'leak_scan.private_markers' list, defaulting to empty (no hardcoded downstream names)",
  "the merge gate scans the candidate's added content and emits an advisory 'WARN:' line on a finding WITHOUT incrementing violations or blocking the merge (gate stays green)",
  "ADR-0005 is updated so the boundary reflects that an advisory leak-scan ships, while mandatory block-on-leak remains roadmap",
  "only added lines are scanned (not the whole tree), so accepted historical residuals are not re-flagged",
  "validate, pytest, ruff, format, mypy stay green; new tests cover the CLI, the diff scanner, the config markers, and the gate WARN",
]
+++

# CR-041: advisory leak-scan-at-merge (provider-neutral)

## Context

The repository is now public. A future merge could introduce a secret or a
private (ДСП) reference into the public history. ADR-0005 already specifies a
best-effort leak-scanner (`scan_for_leaks` in `capture.py`), but nothing runs
it at merge time. A required CI check would bind enforcement to one provider's
CI, which contradicts the project's provider-agnostic stance (GitHub, GitFlic,
self-hosting are all first-class). The provider-neutral boundary is the merge
gate, which every merge-authority wrapper already runs identically.

Because the scanner is heuristic and best-effort (ADR-0005: "heuristics miss
content ... not authorization to publish"), making it fail-closed in the
deterministic governance gate would couple governance to false positives and
imply a guarantee the scanner does not provide. It is therefore advisory.

## Objective

Ship a provider-neutral leak-scan: a reusable diff scanner, a neutral
`agentmarshal leak-scan` CLI (which any provider CI may call), and an advisory
WARN in the merge gate — without blocking merges and without hardcoding any
downstream project's private markers.

## Acceptance Criteria

- [ ] `agentmarshal leak-scan --base <ref> --commit <ref>` scans the added
      content of the candidate diff, prints found categories (never the
      matched secret), exits 1 on a finding and 0 when clean.
- [ ] `capture.py` gains `scan_diff_for_leaks()` reusing `scan_for_leaks()`;
      private markers come from an optional `leak_scan.private_markers` list in
      `project.json`, defaulting to empty.
- [ ] The gate emits an advisory `WARN:` line on a finding without
      incrementing `violations` or blocking the merge.
- [ ] ADR-0005 boundary updated: advisory leak-scan ships; mandatory
      block-on-leak stays roadmap.
- [ ] Only added lines are scanned; accepted historical residuals are not
      re-flagged.
- [ ] `uv run agentmarshal validate`, pytest, ruff, format, mypy stay green;
      new tests cover CLI, diff scanner, config markers, and gate WARN.

## Non-Goals

- Not fail-closed and not a merge blocker — advisory only.
- No provider-specific required CI check (that binds enforcement to one
  provider).
- No hardcoded downstream (car-rental / research) markers — config-driven,
  default empty.
- No history rewriting and no re-scan of the existing tree; forward-only.
- Not the mandatory block-on-leak enforcement — that is a later decision (RFC).
