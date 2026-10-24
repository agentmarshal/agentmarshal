+++
schema = 2
id = "CR-234"
title = "Release 0.6.0: the package version is 0.6.0, CHANGELOG and UPGRADING describe what wave B shipped, the proposals index states what has shipped, the threat model names the command-level refusals that print no stage line, and README names the outbox init writes"
scope = [
  "CHANGELOG.md",
  "UPGRADING.md",
  "README.md",
  "docs/threat-model.md",
  "docs/proposals/README.md",
  "docs/README.md",
  "docs/overview.md",
  "docs/self-hosting-workflow.md",
  "pyproject.toml",
  "uv.lock",
  "src/agentmarshal/__init__.py",
  "tests/test_smoke.py",
]
acceptance = [
  "CHANGELOG.md has a `## 0.6.0 — unreleased` section above 0.5.0 (the release task replaces `unreleased` with the PyPI upload date), grouped by subject, in which every entry names the tasks it comes from and describes only behaviour merged on master; every task completed since v0.5.0 (CR-205 to the last completed task before this one) is either named in an entry or listed in one closing line of documentation-only, tooling and process tasks; the section opens by saying that 0.6.0 changes no record, contract-header or manifest schema, so 0.5.0 and 0.6.0 installations read each other's journals, and points to UPGRADING.md",
  "the 0.6.0 section covers, each checked against the code it describes: executing shared extensions — local grants (`extension trust`/`untrust`/`list`), `stage run` with one result line per stage, `record-ext`, `doctor`'s extension listing and runtime check, the `ext`-kind warning in `validate`, switches read from the base and `extension switch off`, the operational lane and `accept --pause`/`--operational`, stage isolation exactly as docs/threat-model.md states it (nothing stated as enforced that the threat model does not state as enforced), `complete` running the stages and `complete --target`; personal extensions in the clone (CR-233, which lands before this task: describe it from its branch `github/feat/CR-233-impl` and re-check the entry against master once it is merged); status and gate additions (CR-200 to CR-203, CR-208, CR-210, CR-222); outbox skipping files already sent; unmeasured sessions in status and report; OpenSpec 1.15.0 for contributors; and the release audit gate as a project process, not a product feature",
  "the 0.6.0 section has a paragraph stating what was decided but is not in this release — record schema 8 and what waits on it, the user extension scope, `next` and the plan file, the watchdog and monitor, the merge slot and the resolution-mode review — each with the decision or proposal that holds it, and nothing presented as shipped that is not",
  "UPGRADING.md has a 0.5.0 -> 0.6.0 section above 0.4.1 -> 0.5.0: no schema change and no ordering rule for the upgrade; what a project gains and what it must do to use it (a shared extension runs only under a local grant, on a workstation; the operational lane; `complete --target` for a wrapper that completes after the merge); that `outbox check` and `send` now skip files already sent; and, for a project that pins OpenSpec through the extension manifest, that the pin is raised by an extension release — each statement checked against the code",
  "docs/proposals/README.md: every proposal shipped in 0.5.0 or 0.6.0 is shown as shipped with its version (020's acknowledge shipped in 0.5.0 — the row no longer says it has not), and no row says shipped for a proposal that is not; docs/threat-model.md names, beside the unreadable trust.toml, the command-level refusals after which no stage prints a line (an unreadable manifest at the base, an unknown phase, an invalid task id, a sidecar journal), checked against stages.py and cli.py; README.md lists the outbox (`.agentmarshal/upstream/README.md`) among what `init` writes, checked against the code that writes it; docs/README.md's documentation map has a line for each of proposals 044 and 045 like the lines for 041 to 043",
  "release-audit documentation findings are corrected, each statement checked against the code: docs/overview.md describes the gate's lanes as the code has them (journal-only means every path under `.agentmarshal/journal/`; the operational lane exists) and no longer calls 0.4.1 the current release; docs/self-hosting-workflow.md says an operator acceptance covering the findings can satisfy the verdict check and that the journal-only and operational lanes need no review; UPGRADING.md's 0.4.1 -> 0.5.0 note no longer promises an unchanged transcript to a project that declares neither assignment nor agreement (the implementation lane prints the changes_required count line); docs/threat-model.md's open question no longer says nothing covers a symlinked `.agentmarshal/switches.toml` (gate-lanes specifies its refusal)",
  "the package version is 0.6.0 in pyproject.toml, src/agentmarshal/__init__.py and uv.lock, the smoke test asserts it, and `agentmarshal --version` prints it",
  "no statement about 0.5.0 or earlier as history changes, apart from the UPGRADING.md correction above; every link added resolves; no other file changes; the suite and the full CI sequence pass",
]
documents = ["CHANGELOG.md", "UPGRADING.md", "README.md", "docs/threat-model.md", "docs/proposals/README.md", "docs/README.md", "docs/overview.md", "docs/self-hosting-workflow.md"]
decisions = ["ADR-0001", "ADR-0013", "ADR-0014", "ADR-0022"]
+++

# Release 0.6.0

## Context

0.6.0 ships wave B: the executing half of ADR-0013 (shared extensions run
at their stages under local grants, switches, the operational lane,
isolation, accepted pauses, `complete` running stages), status and gate
additions, and fixes from an adopter's findings (outbox skipping sent
files, unmeasured sessions). The operator moved wave A (record schema 8)
to 0.7.0. Before the release freeze the release notes must exist, because
the full-project audit checks the release documentation against the code;
the release order in CONTRIBUTING.md (CR-232) puts this release task
before the freeze and the audit; after the audit only fixes, the audit
file and the release date follow.

Earlier reviews deferred three documentation items to this task: the
proposals index still shows 020's acknowledge as not shipped (an audit
calibration finding), the threat model names only the unreadable
trust.toml among refusals that print no stage line (CR-226
ADV-STAGE-NO-LINE-001), and README omits the outbox from what `init`
writes (CR-226 ADV-DOC-002).

## Objective

A reader of the release notes learns exactly what 0.6.0 does, what an
upgrade from 0.5.0 asks of them, and what is still only decided.

## Acceptance Criteria

As in the header.

## Non-Goals

- The release date and the audit file (after the audit).
- Any code or specification change.
- Rewriting the 0.5.0 or earlier CHANGELOG entries (the UPGRADING 0.4.1 -> 0.5.0 correction above is the one exception).
