# Documentation map

## Adopt AgentMarshal

- [overview.md](overview.md) — learn the product purpose, vocabulary, design, and direction.
- [quickstart.md](quickstart.md) — run the complete AgentMarshal loop on a throwaway repository.
- [sidecar.md](sidecar.md) — decide whether the experimental sidecar journal placement fits your use case.
- [harness-setup.md](harness-setup.md) — configure a coding harness to run the rails with explicit permissions.
- [templates/claude-code-settings.local.json](templates/claude-code-settings.local.json) — copy and adapt a Claude Code local permission-allowlist starting point.
- [github-enforcement.md](github-enforcement.md) — bind the gate to GitHub branch protection and required checks.

## Understand a decision or its history

- [adr/ADR-0001-governance-plane.md](adr/ADR-0001-governance-plane.md) — keep governance separate from the execution harness.
- [adr/ADR-0002-unit-of-isolation.md](adr/ADR-0002-unit-of-isolation.md) — use a task as the unit of isolation.
- [adr/ADR-0003-scope-overlay.md](adr/ADR-0003-scope-overlay.md) — treat scope as a coordination overlay rather than an isolation unit.
- [adr/ADR-0004-journal-data-model.md](adr/ADR-0004-journal-data-model.md) — model contracts as documents and evidence as append-only records.
- [adr/ADR-0005-evidence-capture-and-format.md](adr/ADR-0005-evidence-capture-and-format.md) — understand evidence capture policy, measurements, and attestation format.
- [adr/ADR-0006-actors-and-identity.md](adr/ADR-0006-actors-and-identity.md) — understand declared actors, identity, and multi-operator work.
- [adr/ADR-0007-operator-acceptance.md](adr/ADR-0007-operator-acceptance.md) — understand operator acceptance when work has findings.
- [adr/ADR-0008-journal-placements.md](adr/ADR-0008-journal-placements.md) — compare embedded and sidecar journal placements and their guarantees.
- [adr/ADR-0009-research-findings-lifecycle.md](adr/ADR-0009-research-findings-lifecycle.md) — understand how research tasks land through findings.
- [adr/ADR-0010-process-extensions.md](adr/ADR-0010-process-extensions.md) — understand declared-footprint process extensions.
- [adr/ADR-0011-contract-amendment-visibility.md](adr/ADR-0011-contract-amendment-visibility.md) — understand visible contract amendments and review binding.
- [migration-v1-to-v2.md](migration-v1-to-v2.md) — see what did not carry from the v1 rails into the v2 journal.
- [incidents/2026-08-31-scope-warning-scope-creep.md](incidents/2026-08-31-scope-warning-scope-creep.md) — study the scope-warning change that grew into scope creep and was rolled back.
- [README.md](README.md) — use this map to locate the documentation by reader goal.

## Report or assess a finding

- [proposals/README.md](proposals/README.md) — learn how adopters send findings and how upstream publishes their English digests.
- [proposals/001-review-launcher-loses-the-analysis.md](proposals/001-review-launcher-loses-the-analysis.md) — review the finding about discarded reviewer analysis.
- [proposals/002-scope-ergonomics.md](proposals/002-scope-ergonomics.md) — review the finding about silently unmatched scope.
- [proposals/003-roles-and-actors.md](proposals/003-roles-and-actors.md) — review the deferred proposal for actor-bound scope.
- [proposals/004-provider-ci-integration.md](proposals/004-provider-ci-integration.md) — review the deferred provider-CI integration proposal.
- [proposals/005-research-findings-have-no-record-type.md](proposals/005-research-findings-have-no-record-type.md) — review the finding that led to a research-findings lifecycle.
- [proposals/006-contract-repair-path.md](proposals/006-contract-repair-path.md) — review the finding on repairing a defective contract.
- [proposals/007-accepting-work-over-findings.md](proposals/007-accepting-work-over-findings.md) — review the finding on operator acceptance over findings.
- [proposals/008-session-and-token-accounting.md](proposals/008-session-and-token-accounting.md) — review the proposal for durable session and token accounting.
- [proposals/009-lifecycle-extension-points.md](proposals/009-lifecycle-extension-points.md) — review the deferred lifecycle-extension proposal.
- [proposals/010-executor-artifacts-lifecycle.md](proposals/010-executor-artifacts-lifecycle.md) — review the finding on external-executor artifact lifecycle.
- [proposals/011-windows-journal-directory-acl.md](proposals/011-windows-journal-directory-acl.md) — review the Windows journal-directory access-control finding.
- [proposals/012-upstream-feedback-channel.md](proposals/012-upstream-feedback-channel.md) — review the finding that established the upstream feedback convention.
- [proposals/013-build-tooling-idempotent-artifact-copy.md](proposals/013-build-tooling-idempotent-artifact-copy.md) — review the declined idempotent artifact-copy proposal.
- [proposals/014-init-leaves-trust-preconditions-unchecked.md](proposals/014-init-leaves-trust-preconditions-unchecked.md) — review the finding on unverified trust preconditions after initialization.
- [proposals/015-reviewer-command-contract-undocumented.md](proposals/015-reviewer-command-contract-undocumented.md) — review the finding on the undocumented reviewer-command contract.
- [proposals/016-reviewer-prose-not-durable-in-the-published-release.md](proposals/016-reviewer-prose-not-durable-in-the-published-release.md) — review the finding on non-durable reviewer prose.
- [proposals/017-provider-template-gate-check-structurally-red.md](proposals/017-provider-template-gate-check-structurally-red.md) — review the finding on the provider template's structurally red gate check.
- [proposals/018-session-activity-vocabulary-and-cost.md](proposals/018-session-activity-vocabulary-and-cost.md) — review the finding on session activity vocabulary and cost.
- [proposals/019-journal-transactions-assume-direct-commits.md](proposals/019-journal-transactions-assume-direct-commits.md) — review the finding on journal transactions that assume direct commits.
- [proposals/020-leak-scan-names-no-file-and-self-matches.md](proposals/020-leak-scan-names-no-file-and-self-matches.md) — review the finding on leak-scan locations and self-matches.
- [proposals/021-reviewer-stderr-discarded-on-success.md](proposals/021-reviewer-stderr-discarded-on-success.md) — review the finding on discarded reviewer stderr.
- [proposals/022-amendments-invisible-to-the-reviewer.md](proposals/022-amendments-invisible-to-the-reviewer.md) — review the finding on amendments invisible to reviewers.
- [proposals/023-upstream-outbox-has-no-transaction.md](proposals/023-upstream-outbox-has-no-transaction.md) — review the finding on an outbox without a transaction.

## Contribute a change

- [self-hosting-workflow.md](self-hosting-workflow.md) — follow the task lifecycle AgentMarshal uses to govern its own changes.
