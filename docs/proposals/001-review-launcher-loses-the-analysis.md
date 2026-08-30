# 001 — The review launcher discards the reviewer's analysis

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.1.0 · **Disposition:** accepted

## Finding

`agentmarshal review` asks the reviewer for "an allowed AgentMarshal verdict"
without listing the allowed values, and requires finding *ids* but no
descriptions. Two consequences follow, and they compound.

When the model returns a verdict outside the enum — or a JSON object with one
extra key — validation rejects the record and **the entire run is discarded**:
the reviewer's prose never reaches disk, because the launcher prints only the
record path. The analysis is paid for and lost. Adopter A measured this before
building a wrapper around it: **3 discarded runs out of 7** on one task, **8 of
14** on another.

Even on a successful run the prose is lost by design: the record schema stores
`findings` as plain strings, so a finding arrives as a bare identifier with no
text anywhere. Reviewer token usage is read from the same discarded output, so
accounting loses it too. The command succeeds either way — that is what makes it
dangerous.

Separately, `advisory_findings` exists in the record schema and is validated by
`records.py`, but the review protocol offers no way to produce it: a reviewer
must either promote an advisory remark to blocking or drop it. A field that
cannot be reached is worse than an absent one.

## Proposed

List the allowed verdicts in the prompt; preserve the raw reviewer output even
when validation rejects the verdict; give findings a place for their text; make
`advisory_findings` reachable through the protocol.

## Disposition — accepted

All four are defects in the launcher, not in the adopter's setup, and the first
two are cheap. The lost-analysis one is the most urgent: it silently destroys
paid work and its failure mode looks like success. Losing the finding text also
undercuts the product's own claim — evidence that says only `F-002` is not
evidence. This aligns with an independently recorded upstream finding that the
reviewer is non-deterministic; robustness work will cover both.
