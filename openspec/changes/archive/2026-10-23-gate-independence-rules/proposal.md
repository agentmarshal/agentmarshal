## Why

ADR-0018 decision 3 lets a contract declare the independence rules in force
— the reviewer is not a writer of the candidate, is a different declared
actor than the implementer, a different vendor, a different model — and
ADR-0022 section 5 fixes the vocabulary and says a rule that cannot be
judged reads "not checked". CR-147 landed the schema-3 header that parses
`independence`; nothing reads it yet, so a contract's declaration is a
no-op at the merge boundary.

## What Changes

The gate reads the trusted contract's `independence` and prints one line
per declared rule other than `reviewer-not-writer` — which stays the single
existing identity check whether or not the header names it — judging the
latest review of the candidate's commit against the task's implementer
sessions: the session records whose `commit` is a commit of the candidate's
`merge-base..candidate` range. `distinct-vendor` compares
`reviewer.vendor` against each session's `usage.provider`,
`distinct-model` `reviewer.model` against `model`, and `distinct-actor`
`reviewer.actor` against each session's `actor` declared in the project's
actors table. A rule holds only against every such session; a failing rule
refuses the candidate naming the rule and the two compared values. Where a
rule cannot be judged — no implementer session in range, a compared field
absent on either side, an undeclared actor — the line reads `NOT CHECKED`,
and under `--without-review` the rule lines read `NOT EXAMINED` as the
existing review-bound lines do. A contract declaring no `independence`
produces today's transcript byte for byte.

## Capabilities

- modified: `contract-governance`

## Impact

`src/agentmarshal/journal/gate.py` gains the rule evaluation beside the
existing reviewer-identity check; `parse_contract_text` and the record
model already carry everything the rules need. `status` showing the
declared assignment, and membership checks over `implementers` and
`reviewers`, remain later tasks.
