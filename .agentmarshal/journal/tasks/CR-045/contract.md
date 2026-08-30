+++
schema = 1
id = "CR-045"
title = "honesty: record the declined proposal, state that vendor:human is self-declared"
scope = ["docs/proposals/", "README.md"]
acceptance = [
  "docs/proposals/ gains proposal 013 with disposition 'declined' and its reasoning: the reported defect is in the adopter's own build tooling, not in an agentmarshal command",
  "013 also records that the proposal was dropped rather than declined when the first batch landed, since docs/proposals/README.md states that a declined proposal keeps its file and its reason",
  "docs/proposals/README.md is corrected: the batch table lists 013, the source-to-proposal count matches reality, and the disposition summary is accurate",
  "README.md's trust-boundary paragraph states plainly that a 'human' reviewer is a self-declaration: the gate compares an email string and does not establish that a person reviewed anything, so a record an agent produced with --vendor human is indistinguishable from one a person created",
  "no code, schema or gate change; validate/pytest/ruff/format/mypy stay green",
]
+++

# CR-045: honesty: record the declined proposal, state that vendor:human is self-declared

## Context

Two gaps in the public record, both found by auditing our own work rather than
the tool's.

**The intake dropped a proposal instead of declining it.** CR-044 landed twelve
digests from twenty-two source files, but one source — a defect in an adopter's
own build script — was silently omitted rather than declined with a reason.
`docs/proposals/README.md` says in as many words that a declined proposal keeps
its file and its reason, so the omission contradicts the policy it ships with,
and the stated source-to-proposal count implies a coverage the set does not
have. A batch with zero declines is also a weak triage signal.

**The trust boundary understates one case.** README already says the gate does
not authenticate who recorded a review. What it does not say is the practical
consequence: `--vendor human` is a self-declaration. The gate compares an email
string against the commit authors' — it establishes nothing about a person
having reviewed. This was demonstrated in operation: six review records marked
`vendor: human` were produced by an agent, and every gate passed with
"reviewer is independent of the candidate's writers". Nothing in the evidence
distinguishes them from records a person created. For a tool whose claim is that
independent review becomes a property of the repository, that sentence has to be
in the trust boundary.

## Objective

Make the public record say what is true in both cases: land the declined
proposal with its reasoning and correct the batch summary, and state in the
trust boundary that a human reviewer is self-declared.

## Acceptance Criteria

- [ ] Proposal 013 exists with disposition `declined` and reasoning (defect is
      in the adopter's tooling, not in an agentmarshal command).
- [ ] 013 records that it was dropped rather than declined in the first batch.
- [ ] `docs/proposals/README.md` corrected: table, counts, disposition summary.
- [ ] README trust boundary states that `vendor: human` is self-declared and
      what the gate actually checks.
- [ ] No code/schema/gate change; the suite stays green.

## Non-Goals

- Not adding a `recorded_by` field or any other mitigation — this task states
  the boundary honestly; changing it is separate work.
- Not revisiting the dispositions of proposals 001-012.
