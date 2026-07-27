# GitHub enforcement (Variant 2)

AgentMarshal's gate is provider-agnostic; how the gate *binds* to a merge
is provider-specific. On GitHub the binding is **Variant 2**: the gate
runs as a status check and branch protection blocks the merge until the
required checks are green. This contrasts with the GitFlic **Variant 1**
model, where a merge is invoked (`am-merge`) and the gate is run inline
with an explicit pipeline attestation (see `docs/self-hosting-workflow.md`).

The workflow template is `templates/github/agentmarshal-governance.yml`.

## The model

Under Variant 2 the provider — not the gate — guarantees that the tests
passed: GitHub will not merge until *every* required check is green. The
gate therefore runs with `--attestation ci-required`, which delegates the
pipeline attestation to the provider's required checks instead of
verifying a pipeline SHA itself. This is only sound when the test check is
*also* required for merge — otherwise untested code could merge with only
the gate check green.

## Branch protection

On the protected branch, require:

- **`governance`** — runs `agentmarshal validate` (journal integrity) and
  your project's tests/lint/type checks. Both must be green.
- (Optionally split the tests into their own required check.)

The **`gate`** check is shipped **advisory** (`continue-on-error: true`)
for now — see the open item below. Once review materialisation is in
place, make `gate` a required check too; that is the point at which the
gate becomes the merge authority on GitHub.

## Token permissions

The template declares least-privilege `permissions: contents: read` at the
top level. Pull-request-controlled code (project checks, dependency
install, the PR-head checkout in the gate job) must not inherit
write-capable default token permissions — critical for a public repository
with fork pull requests. Grant additional scopes only to the step that
needs them; the review-materialisation step (below) will need
`pull-requests: read` to read the PR approval.

## Open item: review materialisation (Phase C)

The gate's review-bound lane requires the review evidence to be present in
the checkout it evaluates. In the GitFlic invoked model the reviewer's
verdict is recorded into the working-tree journal just before the merge.
On GitHub, CI evaluates a clean checkout, so the review evidence must be
**materialised from the pull request's approval** — the approving
reviewer's identity and verdict turned into a review record for the exact
head commit — before the gate step runs. That provider integration is
deferred (Phase C).

Until it lands, the `gate` check:

- fully enforces the **journal-only lanes** (openings and completions),
  and the **scope**, **append-only**, **base-state** and **lifecycle**
  checks on every candidate;
- cannot yet enforce the **approved-independent-review** requirement in
  CI, so it is advisory.

This is tied to the gate's **record-provenance trust boundary** (see
`docs/self-hosting-workflow.md`): the gate validates review *contents* and
reviewer independence, but does not authenticate *who* produced a record.
On a public GitHub repository with fork pull requests — an untrusted
launcher/checkout — materialising the review from the provider's own
approval (rather than trusting a record committed by the PR author) is
what makes the review evidence trustworthy. Designing that materialisation
is therefore also a step toward closing the provenance gap for public use.

## Variant 1 vs Variant 2

| | GitFlic (Variant 1) | GitHub (Variant 2) |
|---|---|---|
| Merge trigger | invoked (`am-merge`) | provider merge after required checks |
| Attestation | `--attestation commit` (explicit SHA) | `--attestation ci-required` (delegated) |
| Review evidence | recorded into the working tree at merge | materialised from the PR approval (Phase C) |
| Gate role | authority, invoked | authority, as a required check |

The gate logic is identical across both; only the binding differs — which
is the vendor-neutrality claim in practice.
