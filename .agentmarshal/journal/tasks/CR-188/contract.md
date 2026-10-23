+++
schema = 2
id = "CR-188"
title = "record-session writes a session's start and end, the provider's reset time and a cost, and --if-missing makes a repeat write a no-op"
scope = [
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/session.py",
  "tests/",
  "openspec/changes/record-session-times-cost/",
  "openspec/changes/archive/",
  "openspec/specs/session-activity/",
]
acceptance = [
  "the change record-session-times-cost has a proposal, a design.md and a delta spec on the capability session-activity with ADDED requirements for the flags; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal record-session` takes `--started-at` and `--ended-at` (both or neither), `--resets-at`, and `--cost-amount` with `--cost-currency` and `--cost-source reported|estimated` (all three or none), and writes them through `create_session_record`'s existing parameters; a value the record rules refuse — an unpaired time, a reset time on an outcome other than `provider-limit`, an incomplete or malformed cost — is refused before writing, naming the flag",
  "`--if-missing` makes the write a no-op that prints one line naming the existing record when the task already holds a session with the same `role`, `actor` and `activity`, and writes as usual otherwise; the match is on those three fields and the task, exactly, as ADR-0019 decision 6 states",
  "without any of the new flags the command writes and prints exactly what it does today — a test pins a session written with today's flags as the record the previous release wrote, apart from id and times",
  "no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/session-activity/"]
decisions = ["ADR-0019", "ADR-0022"]
+++

# record-session: times, reset, cost, --if-missing

## Context

ADR-0019 decisions 1, 3 and 4: a session can carry when it started and
ended, the provider's stated reset time on a `provider-limit` session, and
a cost — an amount, a currency and its source — beside its tokens.
Decision 6: `record-session --if-missing` makes a repeat write under the
same task, role, actor and activity a no-op with a message, because
recording cost after completion was measured to double a task's cost on a
retry. ADR-0022 section 2 names the fields; CR-176 landed them in the
record model and `create_session_record` accepts them. The command does
not expose them yet.

## Objective

Time, quota resets and money can be put on a session record from the
command line, and a repeated accounting step cannot double a task's cost.

## Acceptance Criteria

As in the header.

## Non-Goals

- `report` showing lead time, phases, money per currency (later tasks).
- Converting currencies or checking an amount against a price list.
- Raw provider exports to the process log (after 0.5.0).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
