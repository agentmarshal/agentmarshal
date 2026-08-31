+++
schema = 1
id = "CR-058"
title = "A session record says where its token counts came from"
scope = ["src/agentmarshal/journal/records.py", "src/agentmarshal/journal/session.py", "src/agentmarshal/cli.py", "tests/test_journal.py"]
acceptance = [
  "a session record may carry a `usage` object with `provider` and `method`, and nothing else",
  "`method` is one of `reported` or `measured`; any other value is refused",
  "`provider` must be a non-empty string",
  "a session record without `usage` remains valid, so records written by 0.1.0 keep validating",
  "`record-session` accepts `--usage-provider` and `--usage-method` and writes them into the record",
  "supplying one of the two flags without the other is refused, naming the missing one",
  "`agentmarshal validate` accepts a journal containing both shapes of session record",
]
+++

# CR-058: A session record says where its token counts came from

## Context

Adopter proposal 008, raised independently by two adopters in four separate
documents — the strongest convergence this project has received.

The counts themselves are already normalised: a session record carries
`tokens.input`, `tokens.output` and `tokens.cache` as plain integers, not a
provider's raw payload. What the record does not say is **where those numbers
came from**. Adopter B, working with an external executor, reports that usage
has to be reconstructed afterwards from provider logs — a per-project procedure
that is lossy and cannot be verified later. A count a provider reported and a
count someone reassembled from logs are different evidence, and today the record
presents them identically.

The economics claim is one of this project's stated purposes, so a number whose
origin cannot be told apart from a reconstruction weakens exactly the thing the
record exists to support.

The existing `source` field is not this. It is the schema-2 provenance marker
saying how the *evidence* was captured (`live`, `backfill`, …), not which
provider produced the usage figures or whether they were reported or reassembled.

## Objective

Let a session record carry the provenance of its token counts — which provider
they concern, and whether the provider reported them or they were measured
afterwards — without changing the counts themselves and without breaking records
already written.

## Acceptance Criteria

- A session record may carry an optional `usage` object containing exactly
  `provider` and `method`. Any other key in it is refused, and the error names it.
- `method` is one of `reported` (the provider stated these numbers) or `measured`
  (they were reassembled after the fact, for example from logs). Any other value
  is refused.
- `provider` must be a non-empty string.
- A session record with no `usage` at all remains valid — records written by
  0.1.0 must keep validating.
- `record-session` accepts `--usage-provider` and `--usage-method` and writes
  them into the record.
- Supplying only one of the two flags is refused, and the message names the one
  that is missing.
- `agentmarshal validate` accepts a journal holding both shapes of record.

## Non-Goals

- Collecting usage automatically from any provider. This task defines what a
  record can say, not how a number is obtained.
- A vocabulary of provider names. `provider` is free text; constraining it is a
  separate decision and would date badly.
- Changing `tokens`, its three fields, or their arithmetic.
- Changing `agentmarshal report` or how it aggregates.
- Reworking the `source` provenance field or the artifacts list.
