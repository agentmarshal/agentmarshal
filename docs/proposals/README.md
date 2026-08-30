# Proposals from adopters

Findings and change requests from people running AgentMarshal on their own
repositories. These are the most valuable input the project gets: they come from
operation, not from reading code, so they carry failure frequency, the real cost
of workarounds, and which error messages leave an operator with nothing to act
on.

## How a proposal gets here

An adopter collects operational findings in their own repository (the convention
is `.agentmarshal/upstream/`) and sends a batch. Upstream publishes an **English
digest** of each: the finding, its measurements verbatim, what is proposed, and
our disposition. The original stays with the reporter — see
[CONTRIBUTING.md](../../CONTRIBUTING.md) for the language and privacy policy.

Digests, not transcripts, for two reasons. Adopter repositories are private, and
this one is public and cannot un-publish — so reporters appear under a stable
pseudonym with a neutral profile, never a client or product name. And a proposal
usually carries downstream specifics (their scripts, their task numbers) that a
reader here does not need.

**Measurements are quoted verbatim.** Counts, run ratios and timings are the
evidence; the prose around them is ours.

## Disposition

Every proposal carries one, with the reasoning:

- **accepted** — we agree and intend to act; a task or ADR follows.
- **deferred** — real, but not now; the reason is stated.
- **declined** — we do not intend to act; the reason is stated. A declined
  proposal keeps its file. Recording why something was refused is the point of
  the journal, and it applies to incoming proposals too.

A disposition is our judgement, not a fact about the reporter's setup. Where we
think a finding is out of the tool's scope we say so, and where a proposal
changed our roadmap we say that too.

## Current batch

Landed 2026-08-30, from three adopters running 0.1.0 in production. Twenty-two
source files digested into thirteen proposals — eight accepted, four deferred,
one declined. The recurring themes are review protocol robustness, contract
repair, and session/token accounting; the last was raised independently by two
adopters.

| # | Theme | Reporters | Disposition |
|---|---|---|---|
| [001](001-review-launcher-loses-the-analysis.md) | Review launcher discards the reviewer's analysis | A | accepted |
| [002](002-scope-ergonomics.md) | Scope is silently accepted when it matches nothing | A | accepted |
| [003](003-roles-and-actors.md) | Scope is not bound to an actor | A | deferred |
| [004](004-provider-ci-integration.md) | Provider CI integration has slots but no contract | A | deferred |
| [005](005-research-findings-have-no-record-type.md) | Research findings have no record type | A | deferred |
| [006](006-contract-repair-path.md) | A defective contract can only be abandoned | A, B | accepted |
| [007](007-accepting-work-over-findings.md) | The operator cannot accept work over findings | A | accepted |
| [008](008-session-and-token-accounting.md) | Session/token accounting is not in the core | B, C | accepted |
| [009](009-lifecycle-extension-points.md) | No lifecycle extension points for evidence storage | C | deferred |
| [010](010-executor-artifacts-lifecycle.md) | External-executor artifacts have no lifecycle | A | accepted |
| [011](011-windows-journal-directory-acl.md) | Windows: a new task directory can be unreadable | B | accepted |
| [012](012-upstream-feedback-channel.md) | No convention for sending findings upstream | A, B | accepted |
| [013](013-build-tooling-idempotent-artifact-copy.md) | A build script fails when the artifact is already at its target path | B | declined |

## Reporters

| Pseudonym | Profile |
|---|---|
| **Adopter A** | Python web service, Git hosting provider, Linux runner, vendored wheel |
| **Adopter B** | business-application project, Windows host, external executor |
| **Adopter C** | business-application project, Windows host |
