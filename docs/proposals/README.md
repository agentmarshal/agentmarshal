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

## Tracking what happened to yours

A proposal you sent carries three things you can read from here without asking
anyone.

Its **source line** is the sha256 of the file you sent, as sent. It is a one-way
digest: it identifies your original to you, who already hold it, and says
nothing about its content to anyone else. Hash your outbox file and search this
directory for the result, and you have your proposal whatever we numbered it and
whatever we titled it.

Its **disposition** is what we decided, with the reasoning.

The **where** column of a batch table says what an accepted proposal became — a
release, a decision record, or the piece of work that carries it. A disposition
without that column is a promise; with it, it is a place to look.

Sending a batch and then reading this file is the whole protocol today. A
command that reads your outbox, hashes each finding and reports its state back
to you is proposed in [023](023-upstream-outbox-has-no-transaction.md) and
accepted for a later release.

## Batch of 2026-09-16

From one adopter who installed the published 0.3.0 on a new repository and ran
the governed loop on it: the first batch this project has received from a
from-scratch install, which is why it is dense in onboarding defects. Ten source
files, ten proposals, all accepted — two of them in part, with the deferred half
and its reason stated in the proposal. Nine of the ten were still true on the
default branch when the batch was triaged; one had been fixed after the release
and is waiting for it, which is itself the subject of proposal 016.

The recurring theme is what the tool leaves to the operator without saying so:
preconditions it never states, a command contract discoverable only from source,
a shipped template that is structurally red, and its own feedback channel with
no transaction behind it. Two proposals, 020 and 022, describe defects this
project also has in its own journal, and 022 changed the release plan.

| # | Theme | Reporter | Disposition | Where |
|---|---|---|---|---|
| [014](014-init-leaves-trust-preconditions-unchecked.md) | `init` leaves the trust preconditions unchecked | D | accepted | 0.4.0, onboarding |
| [015](015-reviewer-command-contract-undocumented.md) | The reviewer command contract is only in the source | D | accepted | 0.4.0, onboarding |
| [016](016-reviewer-prose-not-durable-in-the-published-release.md) | Reviewer prose is not durable in the published release | D | accepted | 0.4.0 carries the fix |
| [017](017-github-template-gate-check-structurally-red.md) | The template's gate check is red on every implementation PR | D | accepted | 0.4.0, onboarding |
| [018](018-session-activity-vocabulary-and-cost.md) | No activity for a coordinating role, no place for cost | D | accepted *(cost deferred)* | accounting rework |
| [019](019-journal-transactions-assume-direct-commits.md) | Journal transactions assume direct commits to the base | D | accepted | 0.4.0, templates |
| [020](020-leak-scan-names-no-file-and-self-matches.md) | `leak-scan` names no file, and matches its own markers | D | accepted *(third part deferred)* | 0.4.0; a record type decided separately |
| [021](021-reviewer-stderr-discarded-on-success.md) | A reviewer command's stderr is discarded on success | D | accepted | 0.4.0 |
| [022](022-amendments-invisible-to-the-reviewer.md) | Contract amendments are invisible to the reviewer | D | accepted | decision record, then 0.4.0 |
| [023](023-upstream-outbox-has-no-transaction.md) | The outbox has a convention but no transaction | D | accepted | 0.4.0 docs; command later |

## Batch of 2026-08-30

Landed 2026-08-30, from three adopters running 0.1.0 in production. Twenty-two
source files digested into thirteen proposals — nine accepted, three deferred,
one declined. Dispositions dated later than the batch record re-reads. The recurring themes are review protocol robustness, contract
repair, and session/token accounting; the last was raised independently by two
adopters.

| # | Theme | Reporters | Disposition |
|---|---|---|---|
| [001](001-review-launcher-loses-the-analysis.md) | Review launcher discards the reviewer's analysis | A | accepted |
| [002](002-scope-ergonomics.md) | Scope is silently accepted when it matches nothing | A | accepted |
| [003](003-roles-and-actors.md) | Scope is not bound to an actor | A | deferred |
| [004](004-provider-ci-integration.md) | Provider CI integration has slots but no contract | A | deferred |
| [005](005-research-findings-have-no-record-type.md) | Research findings have no record type | A | accepted *(2026-09-01, was deferred)* |
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
| **Adopter D** | greenfield project, Linux host, GitHub, agent-driven loop with three paid roles: a coordinator, an implementer and a model reviewer |
