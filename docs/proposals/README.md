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

A proposal that asks for several things can carry one of these with the part we
are not taking named in parentheses, as 027 and 037 do. The disposition section
of the file itself always says which part is which.

A disposition is our judgement, not a fact about the reporter's setup. Where we
think a finding is out of the tool's scope we say so, and where a proposal
changed our roadmap we say that too.

## Tracking what happened to yours

A proposal you sent carries three things you can read from here without asking
anyone.

Its **source line** is the sha256 of the file you sent, as sent, in full and in
lowercase hex, as every other hash in this project is written. It is one-way: it
identifies your original to you, who already hold it, and says nothing about its
content to anyone else. Hash your outbox file, search this directory for the
result, and you have your proposal whatever we numbered it and whatever we
titled it.

The source line begins with the batch of 2026-09-16. Proposals landed before it
carry no hash, because the convention did not exist when they arrived; their
reporters match them by title, and we will not retrofit hashes onto files whose
originals may since have been edited.

Its **disposition** is what we decided, with the reasoning.

The **where** column of a batch table says what an accepted proposal became — a
release, a decision record, or the piece of work that carries it. A disposition
without that column is a promise; with it, it is a place to look.

Sending a batch and then reading this file is the whole protocol today. A
command that reads your outbox, hashes each finding and reports its state back
to you is proposed in [023](023-upstream-outbox-has-no-transaction.md) and
accepted for a later release.

## Batch of 2026-10-03

Three files from Adopter D — the reporter of the 2026-09-16, 2026-09-18
and 2026-10-01 batches — observed on 0.4.0 in the same agent-driven
loop, now run unattended: a
coordinating agent drives tasks through implementer → review → gate →
completion and deployment, with implementers being three agent CLIs. All
three are published, as proposals 041 through 043.

The recurring theme is the loop around the tool rather than the tool's
records: the next-step decision every adopter rewrites in a driver that
misreads why a step failed; the liveness of an unattended run watched by
hand — where the reporter offers its step watchdog and loop monitor back as
a reference extension, the route by which the code may arrive not yet
decided; and the stale-merge window between review and integration that
makes every approved candidate pay a conflict round and a second review.

| # | Theme | Reporter | Disposition | Where |
|---|---|---|---|---|
| [041](041-the-next-step-of-a-task-is-decided-outside-the-tool.md) | The next step of a task is decided outside the tool | D | accepted *(the command and the failure classes in the tool; the plan a supplied file, the driver the adopter kit)* | `agentmarshal next` and the failure classes — new outcome values and a "report finished" session flag, with the accounting rework — in the tool; the plan file in local state, the reference driver in the adopter kit; not shipped yet |
| [042](042-liveness-of-an-unattended-loop-is-watched-by-hand.md) | Liveness of an unattended loop is watched by hand; watchdog and monitor offered | D | accepted *(in part; actions through the tool declined for the core — met by 041's plan file and the watchdog itself; the offered code in principle, route undecided)* | a `step` stage under [ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)'s rule for new stages — accepted, to be added — manifest-declared activity probes, `stalled`/`safety-limit` outcomes with the accounting rework, the session-id field with the records of a later decision, per-run progress in the process log; not shipped yet |
| [043](043-review-before-integration-makes-every-merge-stale.md) | Review before integration makes every merge stale | D | accepted *(the merge slot a supplied extension enforced via [ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)'s `pre-gate-stop`; the core unchanged)* | the integrate → review → merge order as documentation and in the adopter kit; the slot over an atomic remote ref as a supplied extension; the resolution-only review with the finding-lifecycle decision; the metric with `report` and the accounting rework; not shipped yet |

## Batch of 2026-10-01

Fourteen files from Adopter D — the reporter of the 2026-09-16 and
2026-09-18 batches — observed on 0.3.0 and 0.4.0 in the agent-driven loop
their earlier reports describe, where a coordinating agent writes the
contract, launches the implementer and the reviewer, and records
completion. All fourteen are published, as proposals 027 through 040.

The recurring theme is facts that never become records: advisory findings
with no fate, check outcomes the journal never hears, verdicts that do not
say what was executed, a contract written by an agent and judged by no one
— and around them, an outbox with no scaffold, a journal with no time axis,
a contract that never names its implementer and reviewer, transactions that
sweep other tasks' records, a review that accepts an unfinished candidate,
a crash on a non-UTF-8 diff, an adopter setup that cannot be carried to the
next repository, findings that do not feed back into the next round, and
in-flight steps the journal cannot see. One file in the batch is itself a
withdrawal: the reporter measured a suggestion from an earlier file of the
same batch and took it back.

| # | Theme | Reporter | Disposition | Where |
|---|---|---|---|---|
| [027](027-advisory-findings-have-no-lifecycle.md) | Advisory findings have no lifecycle | D | accepted *(in part; the verdict rename declined)* | the dispositions with the finding-lifecycle decision, and the documentation stating what `approved` means — both accepted, not shipped yet |
| [028](028-check-outcomes-are-not-evidence.md) | Check outcomes are not evidence | D | accepted | the `check` record with the review-evidentiality decision; not shipped yet |
| [029](029-outbox-has-no-scaffold-and-its-name-is-taken.md) | The outbox has no scaffold, and `finding` is taken | D | accepted | one command group with 023 — scaffold, validation, send, status; not shipped yet |
| [030](030-review-verdicts-do-not-say-what-was-executed.md) | A verdict does not say what was executed | D | accepted | the executed-versus-read field with the review-evidentiality decision; not shipped yet |
| [031](031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md) | The contract is written by an agent and judged by no one | D | accepted *(in part; the withdrawal of the third suggestion — accepted in [033](033-contract-review-before-implementation-does-not-pay-off.md))* | the contract hashes accepted, not shipped; the agreement record accepted, not shipped, with the contract-governance decision; the withdrawal accepted in [033](033-contract-review-before-implementation-does-not-pay-off.md) |
| [032](032-the-journal-has-no-time-axis.md) | The journal has no time axis | D | accepted | the documentation sentence on the CI cost of a journal transaction, session duration and lead time with the accounting rework alongside 018 and 024, and exposing the gate's existing journal-only lane to the required check with the journal-transactions work of 019 and 035 — all not shipped yet |
| [033](033-contract-review-before-implementation-does-not-pay-off.md) | Contract review before implementation does not pay off — a measured withdrawal | D | accepted *(the withdrawal of [031](031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md)'s third suggestion)* | nothing to ship; 031 names it |
| [034](034-the-contract-does-not-name-its-implementer-and-reviewer.md) | The contract does not name its implementer and reviewer | D | accepted | `provider-limit` already documented since 0.4.1; the output-limit outcome value, the header fields, the gate checks and the `status` display accepted, not shipped yet — where the assignment lives sits with the undecided contract-governance decision |
| [035](035-journal-transactions-sweep-records-of-other-tasks.md) | Journal transactions sweep other tasks' records | D | accepted | the per-task staging with 019's transaction helper, and the gate warning on another task's `opened`/`amendment` records and the `status` listing of unpublished records with it; not shipped yet |
| [036](036-review-accepts-a-candidate-the-implementer-did-not-finish.md) | Review accepts a candidate the implementer did not finish | D | accepted | the session `commit` field, the refusal in `review` and `gate`, and the `status` display of the producing session; not shipped yet |
| [037](037-review-crashes-on-a-diff-that-is-not-utf-8.md) | `review` crashes on a diff that is not UTF-8 | D | accepted *(a defect; the diff-size limit deferred)* | the decode fix shared with the leak scan of 026's fourth finding — root cause reproduced upstream from the scan side; not shipped yet |
| [038](038-an-adopter-setup-cannot-be-carried-to-the-next-repository.md) | An adopter's tuned setup cannot be carried to the next repository | D | accepted *(the need met by a supplied adopter kit; the profile commands deferred)* | the kit: a standard layout `init` creates, layer templates, a manifest, drift in `doctor`; not shipped yet |
| [039](039-review-findings-do-not-feed-back-into-the-next-round.md) | Review findings do not feed back into the next round | D | accepted *(in part; the self-check and findings base deferred, the plugin interface declined at intake — answered by [ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md))* | finding classes and the `changes_required` count in `status` and the gate output with the finding-lifecycle work, the contract principles as documentation — not shipped yet; the plugin interface: extension stages before the gate per ADR-0013, decided not shipped |
| [040](040-in-flight-steps-are-invisible-and-journal-writes-contend-on-one-checkout.md) | In-flight steps invisible to the journal; journal writes contend on one checkout | D | accepted *(in part; a record or a supplied watcher template for the stuck-step visibility not yet decided)* | the fail-fast rule as documentation, the checkout-free write with the transaction helper of 019 and 035; not shipped yet |

## Batch of 2026-09-24

Two files from Adopter A — one of the first batch's three reporters, named
there on 001 through 007, 010 and 012. The first: before upgrading a pinned
installation from 0.3.0 to 0.4.0 they ran the new wheel's `validate`
read-only over their journal, and it refused records 0.1.0 had written: one
failure line for each of two tasks, over review records whose finding ids are
sentences in which a narrow no-break space separates thousands, and the check
refused every space separator but a plain space. The defect was reproduced
the day it was reported and the fix shipped as 0.4.1. The second file carries
four findings from one task's eight review rounds: a reviewer asserting
external facts it could not check, findings arriving on lines unchanged since
the first round, cost written after `complete` needing idempotency, and a
leak scan a single binary file in the diff switches off.

| # | Theme | Reporter | Disposition | Where |
|---|---|---|---|---|
| [025](025-validate-refused-records-an-earlier-release-wrote.md) | `validate` refused records an earlier release wrote | A | accepted *(in part; the allowlist declined)* | the narrowed rule and the release check in 0.4.1; retroactivity accepted as a principle, mechanism undecided |
| [026](026-reviewer-facts-round-convergence-and-two-gaps.md) | Unchecked reviewer facts, unconverging review rounds, and two further gaps | A | accepted *(in part; `review --since` deferred)* | the protocol wording, `record-session --if-missing` and the per-file leak scan accepted, not yet shipped; the `evidence` field accepted with the review-evidentiality decision, the lifecycle machinery with the finding-lifecycle decision; `review --since` deferred until it settles whether rounds link at all |

## Batch of 2026-09-18

One finding from the reporter of the batch below, after twelve governed tasks
with three executor models: the journal measures tokens, while the provider
stopped work on an allowance of its own, so the evidence pointed away from the
decision it was supposed to support. Accepted; the part deferred at
intake was accepted on 2026-10-01.

| # | Theme | Reporter | Disposition | Where |
|---|---|---|---|---|
| [024](024-provider-quota-stop-cannot-be-recorded.md) | A provider quota stop cannot be recorded | D | accepted *(the reset-time field accepted 2026-10-01)* | 0.4.1 for the outcome value and the tokens-are-not-cost statement; the field with the accounting rework, not shipped yet |

## Batch of 2026-09-16

From one adopter who installed the published 0.3.0 on a new repository and ran
the governed loop on it: the first batch this project has received from a
from-scratch install, which is why it is dense in onboarding defects. Ten source
files, ten proposals, all accepted — two of them in part at intake, with the
deferred half and its reason stated in the proposal; both deferred halves were
accepted on 2026-10-03. Nine of the ten were still true on the
default branch when the batch was triaged; one had been fixed after the release
and is waiting for it, which is itself the subject of proposal 016.

The recurring theme is what the tool leaves to the operator without saying so:
preconditions it never states, a command contract discoverable only from source,
a shipped template that is structurally red, and its own feedback channel with
no transaction behind it. Four of the ten land close to home: 017, 022 and 023
name defects this repository has, and 020 names one it would acquire the day it
declared a marker of its own. A fifth, 019, describes a pattern we solved
privately and never shipped. Two changed what the next release contains: 016
brought it forward, and 022 put a decision record in front of it.

| # | Theme | Reporter | Disposition | Where |
|---|---|---|---|---|
| [014](014-init-leaves-trust-preconditions-unchecked.md) | `init` leaves the trust preconditions unchecked | D | accepted | 0.4.0, onboarding |
| [015](015-reviewer-command-contract-undocumented.md) | The reviewer command contract is only in the source | D | accepted | 0.4.0, onboarding |
| [016](016-reviewer-prose-not-durable-in-the-published-release.md) | Reviewer prose is not durable in the published release | D | accepted *(third request met in another shape)* | 0.4.0 carries the fix, opt-in through the capture policy — see its dated note |
| [017](017-provider-template-gate-check-structurally-red.md) | The shipped template's gate check is red on every implementation PR | D | accepted | 0.4.0, onboarding |
| [018](018-session-activity-vocabulary-and-cost.md) | No activity for a coordinating role, no place for cost | D | accepted *(the cost field accepted 2026-10-03)* | 0.4.0 for the activity; the cost field accepted 2026-10-03, with the accounting rework — not shipped yet |
| [019](019-journal-transactions-assume-direct-commits.md) | Journal transactions assume direct commits to the base | D | accepted | not in 0.4.0; still accepted, see its dated note |
| [020](020-leak-scan-names-no-file-and-self-matches.md) | `leak-scan` names no file, and matches its own markers | D | accepted *(the acknowledged-and-proceed path accepted 2026-10-03)* | 0.4.0 for the first two; the third accepted 2026-10-03, through the decision record that adds the record type — not shipped yet |
| [021](021-reviewer-stderr-discarded-on-success.md) | A reviewer command's stderr is discarded on success | D | accepted | 0.4.0 |
| [022](022-amendments-invisible-to-the-reviewer.md) | Contract amendments are invisible to the reviewer | D | accepted | decision record, then 0.4.0 |
| [023](023-upstream-outbox-has-no-transaction.md) | The outbox has a convention but no transaction | D | accepted | 0.4.0 for the documentation; the command not yet shipped |

## Batch of 2026-08-30

Landed 2026-08-30, from three adopters running 0.1.0 in production. Twenty-two
source files digested into thirteen proposals — ten accepted, two deferred,
one declined. A disposition dated later than the batch records a re-read or a
later decision — 009's date is the day
[ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
answered it. The recurring themes are review protocol robustness, contract
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
| [009](009-lifecycle-extension-points.md) | No lifecycle extension points for evidence storage | C | accepted *(2026-10-03, was deferred — answered by [ADR-0013](../adr/ADR-0013-extensions-stages-scopes-isolation-trust.md))* |
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
| **Adopter D** | greenfield project, Linux host, Git hosting provider, agent-driven loop with three paid roles: a coordinator, an implementer and a model reviewer |
