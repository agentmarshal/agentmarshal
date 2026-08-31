+++
schema = 1
id = "CR-062"
title = "Warn at open time when a task declares no scope"
scope = ["src/agentmarshal/journal/open_task.py", "tests/test_journal.py", "docs/quickstart.md"]
acceptance = [
  "`agentmarshal open` with no `--scope` warns that the task declares no scope and that no change can land until one is declared",
  "the warning goes to stderr and the task is still opened, like the other scope warnings",
  "a task that declares at least one scope entry produces no such warning",
  "the quickstart mentions the empty-scope case where it explains the existing scope warnings",
]
+++

# CR-062: Warn at open time when a task declares no scope

## Context

`--scope` is optional on `agentmarshal open`, so a task can be opened carrying
`scope = []`. That is not the absence of a restriction — it is the strictest
one. The gate matches every changed path against the entries, so with no entries
every path is outside scope and nothing can land at all.

Found while building CR-061: the implementer briefing printed an empty scope as
a dash under "only these paths may change", which reads as "no limits". CR-061
fixed the wording in the briefing, but that is the place the mistake *surfaces*.
The place it is *made* is `open`, which already warns about the two other scope
mistakes worth catching — an entry that names a directory without its trailing
slash, and an entry that matches nothing on disk.

## Objective

Say at open time that a task with no scope cannot land any change, in the same
place and the same manner as the other scope warnings.

## Acceptance Criteria

- `agentmarshal open` with no `--scope` warns that the task declares no scope
  and that no change can land until one is declared.
- The warning goes to **stderr** and the task is still opened — a warning must
  never become a refusal, as with the existing scope warnings.
- A task declaring at least one entry produces no such warning.
- The quickstart mentions the empty-scope case where it explains the existing
  scope warnings.

## Threat model and boundaries

There is no adversary here. `open` runs in the operator's own checkout and this
change adds one message to a list of messages. The project's path protections
guard a different boundary — the gate reading candidate content a contributor
supplies — and none of it applies to a warning about the operator's own
arguments.

Not defects in this task, and not to be guarded against: symlinks, path
traversal or TOCTOU on any scope entry; validation of what a scope entry names
beyond what `scope_warnings` already does.

## Non-Goals

- **Refusing to open a task with no scope.** A warning must not become a
  refusal; the existing warnings are deliberately advisory, and an operator may
  have a reason to open first and declare later by amending.
- Changing the gate, or how an empty scope is enforced. The enforcement is
  correct; only the silence at open time is not.
- Changing the other two scope warnings or their wording.
- Changing `agentmarshal brief`, which CR-061 already handles.
