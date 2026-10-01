+++
schema = 1
id = "CR-121"
title = "The brief states the journal rule as the gate holds it"
scope = [
  "src/agentmarshal/journal/brief.py",
  "tests/test_brief.py",
]
acceptance = [
  "the rule `agentmarshal brief` prints about .agentmarshal/ says that nothing under .agentmarshal/journal/ is the implementer's to edit, and that another file under .agentmarshal/ may change only when the task's scope names it — the rule AGENTS.md states",
  "every rule the brief lists under its heading of rules the tool enforces is one the gate actually checks; a rule the gate does not check is either removed from that list or moved under a heading that does not claim enforcement, checked against src/agentmarshal/journal/gate.py",
  "a test asserts the new rule's text, and a test asserts the old wording 'Do not edit anything under .agentmarshal/' no longer appears in a brief",
  "the brief's other content and order are unchanged, and the full CI sequence passes",
]
+++

# CR-121: the brief states the journal rule as the gate holds it

## Context

`agentmarshal brief` gives the implementer its task, and lists "Rules enforced
by AgentMarshal", among them "Do not edit anything under .agentmarshal/; the
journal is not the implementer's to edit" (CR-061). Two things are wrong with
that line now. It is stricter than practice: tasks legitimately change
`.agentmarshal/project.json` (CR-111) and `.agentmarshal/extensions/openspec.toml`
(CR-120) when their scope names them. And it is not what the gate checks: the
gate holds a candidate to its scope and keeps journal records and artifacts
append-only; it has no rule about `.agentmarshal/` as a whole.

AGENTS.md (CR-117) states the rule as practice has it. A review of CR-117 found
the tool's own brief contradicting it; every implementer receives the brief.

## Objective

The brief tells the implementer the rule the project follows, and claims
enforcement only for what the gate enforces.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change to what the gate checks.
- AGENTS.md, CONTRIBUTING.md and other documents.
