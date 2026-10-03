+++
schema = 1
id = "CR-140"
title = "ADR-0020: the outbox command group"
scope = [
  "docs/adr/ADR-0020-the-outbox-command-group.md",
]
acceptance = [
  "ADR-0020 renders the decision the operator approved (revision 2 of the draft, with the operator's decisions at its end) faithfully and completely: the command group named outbox, not finding; a new draft with the next number, the five fields of CONTRIBUTING as headings and version and environment lines filled from the machine; a check that names the file and the missing field and runs the leak scan, with an exit status a wrapper can refuse on; a send that makes one batch commit of the outbox only, after the check, delivery staying with the operator; a status that compares each file's hash with the Source lines of an index file the operator names, without network; the layout documentation saying the outbox is neither evidence nor journal — no point dropped and none added",
  "the ADR has the form of ADR-0012..0018 including Consequences and Alternatives considered, derived from the decision without adding decision points; it builds on ADR-0009 and ADR-0013 where relevant and answers proposals 012, 023 and 029",
  "every statement about present behaviour matches the file it rests on — what init creates under .agentmarshal/upstream/ and what its README says, that the five fields live in CONTRIBUTING.md, that agentmarshal finding is a research-finding command, the pathspec that keeps the outbox out of journal commits",
  "proposals are referred to as 'proposal NNN' and linked; earlier ADRs are named and linked; nothing names a private document, an adopter, a client or an unpublished release",
  "the full CI sequence passes",
]
+++

# CR-140: ADR-0020 in English

## Context

The operator approved the outbox decision in Russian on 2026-10-03: one
command group that scaffolds, checks, sends and tracks an adopter's findings
for upstream, under a name that does not collide with the research-finding
command.

## Objective

ADR-0020 is published as the operator approved it.

## Acceptance Criteria

As in the header.

## Non-Goals

- Implementing the commands.
- The documentation map line.
