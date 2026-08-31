+++
schema = 1
id = "CR-065"
title = "An acceptance over findings is a record the journal can show"
scope = ["src/agentmarshal/journal/records.py", "src/agentmarshal/journal/acceptance.py", "src/agentmarshal/journal/attestation.py", "src/agentmarshal/journal/status.py", "src/agentmarshal/journal/report.py", "src/agentmarshal/cli.py", "tests/test_acceptance.py", "tests/test_report.py"]
acceptance = [
  "`agentmarshal accept --task <id> --commit <sha> --by <party> --reason <text>` writes an `acceptance` record naming the party, the exact commit, the findings and the reason",
  "the command refuses unless the latest review of that exact commit is non-approving, and the message says what the latest verdict was",
  "the command derives the findings from that review and refuses if the operator supplied any that differ, naming the difference",
  "an acceptance for a task with a terminal record is refused",
  "the record type has a registered predicateType and `agentmarshal validate` accepts a journal containing one",
  "an acceptance does not change the task's projected state",
  "`agentmarshal status <id>` shows the acceptance in the trail and states in the task summary that the task was accepted over findings, naming the party",
  "where the accepting party matches a declared writer of the accepted commit, `status` says the acceptance was self-accepted",
  "`agentmarshal report` distinguishes a task carrying an acceptance from one that closed on an approval",
]
+++

# CR-065: An acceptance over findings is a record the journal can show

## Context

[ADR-0007](../../../docs/adr/ADR-0007-operator-acceptance.md) decided the design;
this task builds the record, the command and the surfaces that display it. The
gate's handling of an acceptance is deliberately **not** here — it follows in its
own task, so that the one change able to weaken the merge authority is reviewed
on its own.

Until that task lands, an acceptance record is evidence the journal can carry
and show, and it changes no decision.

## Objective

Make an acceptance expressible, valid, and visible.

## Acceptance Criteria

- `agentmarshal accept --task <id> --commit <sha> --by <party> --reason <text>`
  appends an `acceptance` record carrying the accepting party, the exact
  reviewed commit, the blocking finding ids being accepted over, and the reason.
- The command **refuses unless the latest review of that exact commit is
  non-approving**, and the refusal names what the latest verdict actually was.
- The findings come from that review. If the caller supplies findings that
  differ from it in either direction, the command refuses and names the
  difference.
- An acceptance for a task carrying a terminal record is refused.
- The record type has a registered `predicateType`, and `agentmarshal validate`
  accepts a journal containing one.
- The projection is unchanged: an open task stays open.
- `agentmarshal status <id>` shows the acceptance in the record trail **and**
  states in the task summary that the task was accepted over findings, naming
  the party — a reader who does not read every record must still see it.
- Where the accepting party matches a declared author or committer of the
  accepted commit, `status` says so in those terms: self-accepted.
- `agentmarshal report` distinguishes a task carrying an acceptance from one
  that closed on an approval.

## Threat model and boundaries

The hazard here is not an attacker. It is that **this feature can make a merge
that was refused look like one that was approved**, which is the single thing
ADR-0007 forbids. Everything worth guarding is about honesty of display and
about the record corresponding to something that was really said:

- an acceptance that could be recorded without a refusal to point at would be a
  path to merge unreviewed work — hence the latest-review rule;
- an acceptance naming a subset of findings would understate what was overridden
  — hence deriving them from the review rather than trusting the caller;
- an acceptance invisible in `status` or `report` would defeat the purpose of
  recording it at all.

The following are **not** defects in this task and must not be guarded against:

- symlinks, path traversal or TOCTOU on the journal path — this command writes
  through the same journal machinery every other command uses, in the operator's
  own checkout;
- the accepting party being unauthenticated. It is a declaration, exactly as
  `reviewer.email` and `recorded_by` are (ADR-0006), and no check here can or
  should pretend otherwise;
- an operator accepting work they wrote. ADR-0007 permits it deliberately; the
  requirement is that it is **visible**, not that it is prevented.

## Non-Goals

- **Changing the gate.** It follows in its own task. Nothing here alters what
  merges.
- Preventing self-acceptance, or any policy layer over who may accept.
- Retaining or parsing the reviewer's prose about the accepted findings.
- Changing review records, verdicts, or how findings are recorded.
