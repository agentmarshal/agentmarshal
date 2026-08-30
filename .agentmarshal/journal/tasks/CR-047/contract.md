+++
schema = 1
id = "CR-047"
title = "align wording with ADR-0006: the independence check compares declared identities"
scope = ["src/agentmarshal/journal/gate.py", "tests/test_gate.py", "docs/quickstart.md", "docs/overview.md"]
acceptance = [
  "the gate's independence line names what it compares — declared reviewer identity against the candidate's declared writers — instead of reading as if human independence had been established",
  "docs/quickstart.md no longer says independence is enforced; it states that the gate compares the declared reviewer email against the commit authors' and that this establishes nothing about a person having reviewed",
  "docs/overview.md's 'Enforced, not assumed' is corrected the same way",
  "the check's behaviour is unchanged: same comparison, same fail-closed refusal; only the wording changes",
  "tests asserting on the old wording are updated and the suite stays green (validate/pytest/ruff/format/mypy)",
]
+++

# CR-047: align wording with ADR-0006

## Context

ADR-0006 decided that identity in the journal is declared, never authenticated,
and required the tool's own output to say so: an unenforceable claim printed as a
`PASS` is worse than no claim, because it is believed. The ADR named the places
that contradict it and left them for this task.

Three of them are user-facing. The gate prints `reviewer is independent of the
candidate's writers`, which reads as if independence had been established;
`docs/quickstart.md` says independence "is enforced"; `docs/overview.md` says
"Enforced, not assumed". All three describe a comparison of two declared email
strings.

This was observed rather than reasoned: six review records marked `vendor: human`
that an agent produced passed that line unchanged.

## Objective

Make the wording match what the check does, without changing what it does.

## Acceptance Criteria

- [ ] Gate line names the comparison of declared identities.
- [ ] `docs/quickstart.md` states the comparison and its limit.
- [ ] `docs/overview.md` corrected likewise.
- [ ] Behaviour unchanged — same comparison, same fail-closed refusal.
- [ ] Tests updated; suite green.

## Non-Goals

- Not adding `recorded_by` or any policy — those follow separately.
- Not weakening the check: it stays fail-closed exactly as it is.
