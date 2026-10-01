+++
schema = 1
id = "CR-117"
title = "AGENTS.md states the rules an agent implementing a task here follows"
scope = [
  "AGENTS.md",
  "CONTRIBUTING.md",
]
acceptance = [
  "AGENTS.md exists at the repository root, in English and under 8 KB, and states the rules an agent implementing a task in this repository follows: change only the paths in the contract's scope and name any needed path outside it as a departure instead of changing it; create, change or delete nothing under .agentmarshal/; when a harness commits for it, run no git commit, push, branch switch or history rewrite; check every statement about what code or a document does against the file rather than from memory",
  "AGENTS.md says how to read the task — the contract under .agentmarshal/journal/tasks/<id>/contract.md and `agentmarshal brief --task <id>` — and that a task carrying an OpenSpec change implements it without archiving it and without editing openspec/specs/",
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

## Non-Goals

- Rules for whoever coordinates tasks — contracts, journal transactions,
  merges: that is CONTRIBUTING's and the governance documents' business.
- Any change in behaviour or in the check sequence itself.
- Naming a particular agent product or model.
