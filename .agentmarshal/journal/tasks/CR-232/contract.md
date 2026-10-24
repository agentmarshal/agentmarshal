+++
schema = 2
id = "CR-232"
title = "The release workflow refuses to publish a version without a recorded full-project audit whose blocking findings are each dispositioned and whose later changes are only their fixes and the release notes"
scope = [
  ".github/workflows/release.yml",
  ".github/scripts/check_release_audit.py",
  "tests/",
  "CONTRIBUTING.md",
  "release/",
]
acceptance = [
  "`.github/workflows/release.yml` runs `.github/scripts/check_release_audit.py <version>` after the existing tag/version checks and before building, and fails the job — nothing is built or published — when the script refuses",
  "the script reads `release/audit-<version>.toml` from the tagged tree (format documented in CONTRIBUTING.md: `version`, `audited_commit`, `model`, `audited_at`, and one `[[finding]]` per blocking finding with `id`, `disposition` = `fixed` | `deferred` | `rejected`, `task` (a `CR-<n>`, required for `fixed`) and `reason` (required for `deferred` and `rejected`); a finding's description may be withheld) and refuses, naming the cause, when: the file is missing or malformed; `version` differs from the tag; `audited_commit` is not an ancestor of the tagged commit; `model` is not in the script's allowlist (`gpt-6-astra`); a `fixed` finding's task has no `completed` record in the journal; or a path changed between `audited_commit` and the tagged commit lies outside the union of `.agentmarshal/journal/`, `release/`, `CHANGELOG.md`, `UPGRADING.md`, `pyproject.toml`, `uv.lock`, `src/agentmarshal/__init__.py` and the scopes (read from their contracts in the tagged tree's journal) of the tasks the file lists as `fixed`",
  "the script uses only the standard library and git, runs under the workflow's Python, prints one line per refusal and `release audit: passed` on success, and is covered by tests that build small repositories for every refusal and for a pass (zero findings; findings fixed by a task whose scope covers the later change)",
  "CONTRIBUTING.md's release section states the order — release task, freeze, full-project audit with the allowlisted model, blocking findings fixed by ordinary tasks with ordinary review or dispositioned, the audit file, tag — and that the next audit is the next release's, with no re-audit of the fixes; what counts as a blocking audit finding (a broken published decision or threat-model promise, a security defect, a false statement in the release documentation)",
  "no product code changes; the suite and the full CI sequence pass",
]
documents = ["CONTRIBUTING.md"]
decisions = ["ADR-0001", "ADR-0005"]
+++

# Release audit gate

## Context

Operator decision of 2026-10-24: every release is accepted through a full
audit of the project by a strong model (`gpt-6-astra`), enforced by a
release gate. Before the audit, a change freeze; after it, blocking
findings are fixed as ordinary tasks with ordinary review — no re-audit
loop; the next audit is the next release's. The gate therefore cannot
demand "nothing changed since the audit"; it demands that what changed is
the fixes of dispositioned findings and the release notes. The audit's
full text may carry undisclosed security detail and stays private; the
file the gate reads holds the dispositions.

## Objective

A version cannot reach PyPI without an audit whose blocking findings were
each dealt with, and without anything but those fixes landing after it.

## Acceptance Criteria

As in the header.

## Non-Goals

- An audit feature for adopters in the product (a later decision, with an
  ADR).
- Running the audit itself (coordinator tooling).
