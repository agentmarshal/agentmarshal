+++
schema = 2
id = "CR-246"
title = "Stage run refuses a file-form manifest the base cannot read, leak-scan masks the paths in its acknowledgement diagnostics, the operational lane refuses a shared name in --skip-ext, and the release notes disclose the unimplemented runtime lookup and the git 2.31 minimum"
scope = [
  "src/agentmarshal/stages.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "docs/threat-model.md",
  "docs/quickstart.md",
  "docs/sidecar.md",
  "README.md",
  "CHANGELOG.md",
  "UPGRADING.md",
  "release/",
]
acceptance = [
  "`stage run` (and `complete`, through the shared runner) reads every shared extension manifest at the base — file form included — through the base-tree reader, so a file-form manifest the reader refuses fails the command naming the extension and its tree source, as extension-stages requires; file-form extensions still plan no stages (comparison finding SOL-extensions-2); a test with a broken and a command-declaring file-form manifest at the base",
  "`leak-scan`'s diagnostic when it cannot read acknowledgements prints the path masked by the configured private markers and display-escaped (`safe_path` + `escape_for_display`), as the leak-scan spec requires of every path the scan prints (SOL-commands-2); a test with a marker in a task directory name",
  "on the operational lane, `stage run --skip-ext <shared name>` and `complete --skip-ext <shared name>` are refused before any stage is planned, like on every other lane (extension-stages: naming a shared extension in --skip-ext is refused), using only the extension names at the base, not their manifests (SOL-docs-claims-1-1); tests for both commands",
  "docs/threat-model.md and CHANGELOG.md's 'what 0.6.0 leaves out' state that stage run does not yet look up a wrapper's declared runtime or name its path and version (ADR-0013 decision 13 as amended; doctor does): stages run with PATH=/usr/bin:/bin (SOL-extensions-1)",
  "README.md, docs/quickstart.md and docs/sidecar.md name git 2.31 or newer as a requirement (local-state resolution uses --path-format=absolute; complete needs it) (SOL-docs-claims-1-3)",
  "release/audit-0.6.0.toml gains one [[finding]] per finding above — SOL-extensions-1, SOL-extensions-2, SOL-commands-2, SOL-docs-claims-1-1, SOL-docs-claims-1-3 — disposition fixed, task CR-246, with a comment that they come from a gpt-6.1-sol measurement audit of the same commits run after the release audit; CHANGELOG's audit-fixes paragraph names CR-246; `python3 .github/scripts/check_release_audit.py v0.6.0` in a throwaway clone with a local tag prints `release audit: passed`",
  "UPGRADING.md's 0.5.0 -> 0.6.0 section says that `outbox check` and `outbox send` now refuse a file whose bytes git would stage differently from the checked bytes (core.autocrlf, a text/eol attribute or a clean filter on the outbox) and names the remedy (`.agentmarshal/upstream/** -text` in .gitattributes; no filter on the outbox); README.md's capture sentence says precisely that a launcher refusal of malformed reviewer output keeps the raw output at any capture level (CR-245 review advisories)",
  "no other behaviour changes; existing transcripts unchanged; the suite and the full CI sequence pass",
]
documents = ["docs/threat-model.md", "README.md", "CHANGELOG.md", "release/"]
decisions = ["ADR-0013", "ADR-0021"]
+++

# Fixes from the sol measurement audit

## Context

After the release audit, a measurement audit with gpt-6.1-sol over the same
areas and commits (operator decision 2026-10-26) reported findings that a
verification run confirmed at current master: a file-form manifest the base
cannot read is skipped in silence by stage run; leak-scan's acknowledgement
diagnostic prints a path with a private marker unmasked; the operational
lane accepts a shared name in --skip-ext; ADR-0013's runtime lookup at
stage run is neither implemented nor disclosed; the git 2.31 minimum is not
named. The operator decided to fix them before the release.

## Objective

0.6.0 ships without these known defects, and the audit record lists them.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing the runtime lookup at stage run (0.7.0).
- The advisory findings (process-log unreadable file, draft number reuse,
  switched-off extension with a broken manifest) — 0.7.0.
