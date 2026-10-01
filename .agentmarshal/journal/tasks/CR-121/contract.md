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
  "each rule the brief lists sits under a heading that says truthfully whether the gate checks it, verified against src/agentmarshal/journal/gate.py: under the heading of rules the gate checks — the candidate stays within the scope; journal records and artifacts are append-only; merging requires an approving review of this exact commit; under the heading of rules the project follows — satisfy every acceptance criterion, which the gate does not check and the reviewer judges; and the journal rule of criterion 1",
  "a test asserts the new rule's text, and a test asserts the old wording 'Do not edit anything under .agentmarshal/' no longer appears in a brief",
  "the brief's content outside its lists of rules is unchanged, each rule's text is asserted by one test rather than repeated across several, and the full CI sequence passes",
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

## Amended 2026-10-01

Criteria 2 and 4 contradicted each other on one line. Criterion 2 required every
rule under the enforcement heading to be one the gate checks; criterion 4 kept
the brief's order and content unchanged — and the line "Satisfy every
acceptance criterion" sat under that heading. The gate does not check
acceptance criteria; it requires an approving review, and the reviewer judges
the criteria. Two review rounds pulled the line in opposite directions. The
criteria now give the classification itself: what the gate checks — scope,
append-only evidence, an approving review of the exact commit — and what the
project asks without the gate checking it. Criterion 4 now freezes only the
brief outside its rule lists, and asks for one test per rule text.

## Non-Goals

- Any change to what the gate checks.
- AGENTS.md, CONTRIBUTING.md and other documents.
