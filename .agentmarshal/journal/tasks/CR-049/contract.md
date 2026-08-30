+++
schema = 1
id = "CR-049"
title = "warn when a declared scope entry matches nothing"
scope = ["src/agentmarshal/journal/open_task.py", "src/agentmarshal/cli.py", "tests/test_journal.py", "docs/quickstart.md"]
acceptance = [
  "opening a task warns when a scope entry names an existing directory without its trailing slash, naming the corrected form — this is the reported failure",
  "it also warns when an entry matches no path in the working tree, and when an entry is empty",
  "the warning is deliberately bounded: it catches those mistakes and is not a path validator, so unusual entry forms are outside its stated scope and are not warned about",
  "opening still succeeds — a scope may legitimately name a path the task will create, so this is a warning and never a refusal",
  "docs/quickstart.md states the trailing-slash rule where scope is introduced",
  "validate/pytest/ruff/format/mypy stay green with tests covering the directory-without-slash case, an absent path, an empty entry, and a matching entry staying silent",
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

## Amendment (2026-08-31)

The original criteria said the warning fires "for each scope entry that matches
nothing" — a claim quantified over an unbounded space, which a reviewer can
always falsify with one more path form. Five review rounds followed, the last
three adding a path taxonomy (repeated slashes, symlink ancestors, backslashes)
that this contract never asked for and that no stated threat needs.

The criteria are now bounded to what can be demonstrated, and the boundary is
itself a criterion. See `docs/incidents/` for the incident record.

## Non-Goals

- Not refusing an unmatched scope: a task may legitimately declare a path it is
  about to create.
- Not a path validator: entries in unusual forms (repeated slashes, symlinked
  ancestors, non-normalised paths) are out of scope. No stated threat requires
  the tool to police them, and a warning that fires on legal input teaches
  people to ignore warnings.
- Not changing how the gate compares scope entries.
- Not adding cross-task scope-overlap detection (ADR-0006 leaves that advisory
  and later).
