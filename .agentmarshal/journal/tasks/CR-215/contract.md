+++
schema = 2
id = "CR-215"
title = "accept --pause records acceptance of an extension's pause and accept --operational records acceptance of an operational CR"
scope = [
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/acceptance.py",
  "tests/",
  "openspec/changes/accept-pause-operational/",
  "openspec/changes/archive/",
  "openspec/specs/operator-acceptance/",
]
acceptance = [
  "the change accept-pause-operational has a proposal, a design.md and a delta spec on the capability operator-acceptance with ADDED requirements (MODIFIED where a requirement says nothing writes the forms yet); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal accept --task <id> --commit <rev> --pause <extension> --by <party> --reason <text>` writes an acceptance carrying `accepted_pause` for that extension, bound by `accepted_commit` to the resolved commit, with no findings, through `create_acceptance_record`'s existing parameter (ADR-0013 decision 5); the extension must be a shared extension the working tree declares, or the command refuses naming it",
  "`agentmarshal accept --task <id> --commit <rev> --operational --by <party> --reason <text>` writes an acceptance carrying `operational: true` bound to the commit (ADR-0013 decision 17); the task is not required to have a review",
  "the three forms — over findings (today's), `--pause`, `--operational` — are mutually exclusive and exactly one is required, each refusal naming the flags; `--finding` and `--accepted-finding` are refused with `--pause` or `--operational`; acceptance over findings behaves exactly as today, which the existing tests demonstrate unchanged",
  "a refusal writes nothing; the gate is unchanged (it reads no pause or operational acceptance yet); no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/operator-acceptance/"]
decisions = ["ADR-0007", "ADR-0013", "ADR-0022"]
+++

# accept: an extension's pause, an operational CR

## Context

ADR-0013 extends where an operator acceptance may stand, twice: over an
extension's pause (decision 5 — a pause raises no review finding, so the
acceptance stands over the pause itself) and over an operational CR
(decision 17 — an adopter may require acceptance instead of the fast lane;
an operational CR carries no review). ADR-0022 section 2 gives the fields:
`accepted_pause: {extension}` and `operational: true`, each bound by
`accepted_commit`. CR-173 landed them in the record model and
`create_acceptance_record` accepts them; `accept` cannot write them.
ADR-0007's acceptance over findings stays as it is.

## Objective

An operator can put either new form of acceptance on the record with the
command that already records acceptances.

## Acceptance Criteria

As in the header.

## Non-Goals

- The gate or the stage runner reading these acceptances (later tasks).
- Opening an operational CR (`extension switch off`, a later task).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
