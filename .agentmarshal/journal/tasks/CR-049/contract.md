+++
schema = 1
id = "CR-049"
title = "warn when a declared scope entry matches nothing"
scope = ["src/agentmarshal/journal/open_task.py", "src/agentmarshal/cli.py", "tests/test_journal.py", "docs/quickstart.md"]
acceptance = [
  "opening a task warns on stderr for each scope entry that matches nothing in the working tree, naming the entry",
  "the warning is specific when the cause is the missing trailing slash: an entry without a slash that names an existing directory is called out with the corrected form, because that is the reported failure",
  "opening still succeeds — a scope may legitimately name a path the task will create, so this is a warning and never a refusal",
  "the contract written to disk is unchanged by the warning, and the opened record is unaffected",
  "docs/quickstart.md states the trailing-slash rule where scope is introduced",
  "validate/pytest/ruff/format/mypy stay green with tests covering the directory-without-slash case, a genuinely absent path, and a matching entry staying silent",
]
+++

# CR-049: warn when a declared scope entry matches nothing

## Context

Adopter proposal 002. `agentmarshal open --scope <directory>` written without a
trailing slash produces a contract that matches nothing: scope entries are
compared as directory prefixes only when they end in `/`, and as exact paths
otherwise. A task opened as `--scope src` therefore gates every file under
`src/` as out-of-scope.

Nothing says so at open time. The failure surfaces later, at the merge gate, on
a change that is in fact correct — the most expensive moment to find it — and
repairing it needs a second, non-obvious step, because the contract is read from
the base side and must be amended through its own journal-only transaction.

A silent no-op is the worst kind of misconfiguration: fail-closed gating is only
worth having if what is being enforced is what the author meant.

## Objective

Tell the author at open time when a declared scope entry matches nothing, and
name the trailing-slash case explicitly, without refusing the opening.

## Acceptance Criteria

- [ ] Warning per unmatched scope entry, naming the entry.
- [ ] Specific message for a directory named without its trailing slash.
- [ ] Opening still succeeds; warning only.
- [ ] Contract and opened record unaffected.
- [ ] `docs/quickstart.md` states the trailing-slash rule.
- [ ] Suite green; tests cover slash-less directory, absent path, silent match.

## Non-Goals

- Not refusing an unmatched scope: a task may legitimately declare a path it is
  about to create.
- Not changing how the gate compares scope entries.
- Not adding cross-task scope-overlap detection (ADR-0006 leaves that advisory
  and later).
