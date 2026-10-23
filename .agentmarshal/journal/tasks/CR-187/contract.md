+++
schema = 2
id = "CR-187"
title = "agentmarshal acknowledge records that a leak-scan hit on a candidate was reviewed and is not a leak, refusing a hit the scan does not report"
scope = [
  "src/agentmarshal/acknowledge.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/acknowledge-command/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
]
acceptance = [
  "the change acknowledge-command has a proposal, a design.md and a delta spec on the capability leak-scan with ADDED requirements for the command; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal acknowledge --task <id> --base <ref> --commit <rev> --file <path> (--signature <id> | --marker <n>) --reason <text>` writes one `acknowledgement` record through `create_acknowledgement_record`, the commit resolved to its full 40-hex id; the command is registered from its own module the way the `step` group is",
  "before writing, the command runs the same added-content scan `agentmarshal leak-scan --base --commit` runs, with the project's private markers, and writes only when the scan reports a hit with exactly that file — as the scan prints it — and that identification; otherwise it refuses naming the file and identification it was given and how many hits the scan did report, never the matched text",
  "a refusal — unknown or terminal task, commit or base not found, both or neither of `--signature` and `--marker`, a value the record rules refuse (the reason's 1000-character bound included), a hit the scan does not report — writes nothing; a recorder that is not a declared actor is accepted and the output says so",
  "`leak-scan`'s exit status and output are unchanged by this task (honouring acknowledgements is a later task); no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/leak-scan/"]
decisions = ["ADR-0021", "ADR-0022"]
+++

# agentmarshal acknowledge

## Context

ADR-0021: an operator who has verified a leak-scan hit records an
acknowledgement bound to the candidate's commit, the file and the hit's
identification exactly as the scan prints it — a signature id or a private
marker's number, never the matched text — with a reason; any declared actor
may record it, and self-acknowledgement is permitted and marked. ADR-0022
section 3 gives the record (`commit`, `file`, `signature` or `marker`,
`reason` up to 1000 characters, `recorded_by` required). CR-170 landed the
record; nothing writes it.

An acknowledgement matches a hit only on the same commit, file and
identification (ADR-0021 decision 2). A record naming a hit the scan never
reported would match nothing and say something false, so the command
checks the hit against the scan before writing.

## Objective

An operator can put on the record, with one command, that a specific
reported hit was looked at and is not a leak.

## Acceptance Criteria

As in the header.

## Non-Goals

- `leak-scan` and the gate honouring and marking acknowledged hits (later
  tasks).
- Acknowledging an artefact refusal: it names no file (ADR-0021 decision 2).
- Roles or any rule about who may acknowledge (ADR-0021 decision 4).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
