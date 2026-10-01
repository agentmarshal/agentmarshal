+++
schema = 1
id = "CR-117"
title = "AGENTS.md states the rules an agent implementing a task here follows"
scope = [
  "AGENTS.md",
  "CONTRIBUTING.md",
]
acceptance = [
  "AGENTS.md exists at the repository root, in English and under 8 KB, and states the rules an agent implementing a task in this repository follows: change only the paths in the contract's scope and name any needed path outside it as a departure instead of changing it; create, change or delete nothing under .agentmarshal/journal/, and change another file under .agentmarshal/ only when the contract's scope names it; when a harness commits for it, run no git commit, push, branch switch or history rewrite; check every statement about what code or a document does against the file rather than from memory",
  "AGENTS.md says how to read the task — the contract under .agentmarshal/journal/tasks/<id>/contract.md and `agentmarshal brief --task <id>` — and, for a task carrying an OpenSpec change: archive the change only when the contract's scope names openspec/changes/archive/ and the affected openspec/specs/<capability>/ directory, and then only with the archive command; never edit a file under openspec/specs/ by hand; a new capability's Purpose is written in the change's delta, because the archive command leaves it as a placeholder otherwise",
  "AGENTS.md gives the exact check sequence CONTRIBUTING.md gives, with no path arguments, and asks for a final report: what changed in each file, the result of each check, and any acceptance criterion not met with the reason",
  "AGENTS.md names no path outside the repository and no tool that is not published, and CONTRIBUTING.md links to it from the section on development",
  "the full CI sequence passes",
]
+++

# CR-117: AGENTS.md

## Context

From this release on, tasks in this repository are implemented by an agent
working in the task's own worktree, launched by a harness that commits the
result. The rules it follows have so far travelled in each launch prompt. A
file at the repository root carries them once, and `AGENTS.md` is the name
agent tools look for — so the same file also serves an outside contributor
whose own agent opens this repository.

## Objective

An agent that opens this repository finds, in one short file, what it may
change, what it must not touch, how to check its work and what to report.

## Acceptance Criteria

As in the header.

## Amended 2026-10-01 (the journal, not all of .agentmarshal/)

Criterion 1 forbade any change under `.agentmarshal/`. That directory also holds
configuration a task may legitimately change — the project file and extension
manifests (CR-111 changed `.agentmarshal/project.json`; CR-120 changes
`.agentmarshal/extensions/openspec.toml`). What an implementer must never touch
is the evidence journal; the rest follows the contract's scope like any path.

## Amended 2026-10-01

Criterion 2 required that a task implement its OpenSpec change without archiving
it. The implementer found it contradicts practice: CR-105, CR-111 and CR-114
named `openspec/changes/archive/` and the capability's spec directory in scope
and archived in the same candidate. From this release the coordinator writes no
code, so the archive step belongs to the implementer, under the scope the
contract gives — and the baseline spec is only ever written by the archive
command. A new capability's Purpose must be in the delta: archiving without one
writes a placeholder (it happened on CR-114).

## Non-Goals

- Rules for whoever coordinates tasks — contracts, journal transactions,
  merges: that is CONTRIBUTING's and the governance documents' business.
- Any change in behaviour or in the check sequence itself.
- Naming a particular agent product or model.
