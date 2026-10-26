+++
schema = 2
id = "CR-245"
title = "Release 0.6.0 audit record: release/audit-0.6.0.toml lists every blocking finding of the full-project audit with its disposition, and the 0.6.0 notes name the audit fixes and carry the release date"
scope = [
  "release/",
  "CHANGELOG.md",
  "UPGRADING.md",
  "README.md",
  "docs/proposals/012-upstream-feedback-channel.md",
  "docs/harness-setup.md",
  "docs/templates/claude-code-settings.local.json",
]
acceptance = [
  "release/audit-0.6.0.toml follows the format in CONTRIBUTING.md: version = \"0.6.0\", audited_commit = the freeze commit (full 40-character hash), model = \"gpt-6-astra\", audited_at = the time the last area ran, and one [[finding]] per blocking finding of every area — id, disposition, task for fixed, reason for deferred and rejected — exactly as the coordinator's disposition table below lists them; a TOML comment above the findings says which areas ran at which commit (gate-journal at 15af26e before the freeze by operator decision; the others at the freeze commit), that docs-claims ran in two parts, and which finding came from the comparison audit (AUD-whole-project-1, Claude Fable)",
  "`python3 .github/scripts/check_release_audit.py v0.6.0` run against a repository where this task's candidate is merged and tagged prints `release audit: passed` (the report shows the command and its output)",
  "CHANGELOG.md: the 0.6.0 section's heading carries the release date instead of `unreleased` (the date the coordinator gives in the frame), and its audit-fixes paragraph names every audit fix task that completed (CR-235 to CR-244), each described from the code, and the closing line of documentation-only and process tasks is complete; UPGRADING.md changes only if an audit fix changes what an upgrade asks",
  "README.md no longer says capture level `off` keeps nothing: `off` applies to an accepted verdict's prose, while a refused verdict's raw output is preserved at any level (review.py _reject) (CR-243 ADV-readme-capture-off-1); docs/proposals/012's old 'Not yet done' line is marked as superseded by its Where section, without rewriting the dated history (CR-243 ADV-012-stale-disposition-line)",
  "docs/harness-setup.md and the template's comment classify subcommands, not whole groups: `outbox check`, `outbox status` and `extension list` only read; the template allows the bare `agentmarshal gate` as well as `gate` with arguments, matching harness-setup.md (CR-244 ADV-outbox-extension-group-granularity, ADV-template-bare-gate-not-allowlisted)",
  "no other file changes; the suite and the full CI sequence pass",
]
documents = ["release/", "CHANGELOG.md", "README.md", "docs/proposals/012-upstream-feedback-channel.md", "docs/harness-setup.md"]
decisions = ["ADR-0001"]
+++

# Release 0.6.0: audit record

## Context

CONTRIBUTING.md (CR-232): the release workflow refuses to publish without
`release/audit-<version>.toml`, whose blocking findings are each fixed by
a completed task, deferred or rejected with a reason, and after whose
audited commit only those fixes, the release notes and the version
changed. The full-project audit of 0.6.0 ran in four areas with
gpt-6-astra (gate-journal at 15af26e before the freeze by operator
decision, the others at the freeze commit dff244b); docs-claims ran in two
parts by operator decision. The coordinator's disposition table is in
the frame.

## Objective

The release gate can pass on the tagged commit, and the notes say what the
audit changed.

## Acceptance Criteria

As in the header.

## Non-Goals

- The tag, the publication, the GitHub Release (coordinator steps after
  this task).
- Any code change.
