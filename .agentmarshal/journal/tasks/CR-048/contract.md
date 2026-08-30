+++
schema = 1
id = "CR-048"
title = "review protocol: name the verdicts, keep the analysis, reach advisory_findings"
scope = ["src/agentmarshal/journal/review.py", "tests/test_review_launcher.py", "docs/quickstart.md"]
acceptance = [
  "the review prompt lists the allowed verdicts, taken from the single definition in records.py rather than restated, so the prompt cannot drift from what validation accepts",
  "when the reviewer's output fails validation the raw output is preserved and its location named in the error, so a rejected verdict no longer discards the analysis that was paid for",
  "advisory_findings is reachable through the protocol: the verdict object accepts it as an optional key and it reaches the recorded review",
  "an unrecognised key is still refused fail-closed, but the error names the offending key instead of reporting a generic shape failure",
  "docs/quickstart.md's verdict protocol section matches the implemented protocol",
  "validate/pytest/ruff/format/mypy stay green, with tests covering preservation on failure, advisory pass-through, and the named unknown key",
]
+++

# CR-048: review protocol: name the verdicts, keep the analysis, reach advisory_findings

## Context

Adopter proposal 001 reports three defects in the review launcher, and this
project has hit all three while doing the work that documented them.

The prompt asks for "an allowed AgentMarshal verdict" without listing the
allowed values, although `records.py` defines them exactly. A reviewer that
guesses wrong fails validation — and then the second defect applies: the raw
output is discarded, so the analysis is gone. The launcher prints only the
record path, so nothing else holds it. The reporter measured 3 discarded runs
out of 7 on one task and 8 of 14 on another; on the task that documented this,
one run produced no record at all.

Third, `advisory_findings` is in the record schema and `create_review_record`
accepts it, but the parser requires the verdict object to carry exactly three
keys, so the field cannot be produced through the protocol and any extra key
kills the run with a generic message.

## Objective

Stop the launcher from destroying work it has already paid for, and let the
protocol reach what the schema already supports.

## Acceptance Criteria

- [ ] Prompt lists the verdicts from the single definition in `records.py`.
- [ ] Raw output preserved on validation failure, path named in the error.
- [ ] `advisory_findings` accepted as an optional verdict key and recorded.
- [ ] Unknown key still refused, but named in the error.
- [ ] `docs/quickstart.md` protocol section matches the implementation.
- [ ] Suite green; tests cover preservation, advisory pass-through, named key.

## Non-Goals

- Not giving findings a text field — that is a record-schema change and is
  tracked separately.
- Not changing which verdicts are allowed, nor the gate's use of them.
- Not adding retry or quorum behaviour for a non-deterministic reviewer.
