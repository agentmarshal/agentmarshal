## Why

The gate lists what a candidate changes with `git diff --name-only`, and git
shows a rename there by its destination alone. A candidate whose scope covers
the destination can therefore move a file out of a location its scope does not
cover — the source's deletion is never held against the scope. The same listing
decides the lane: a move of a non-journal path to under `.agentmarshal/journal/`
reads as a journal-only candidate and skips the scope check altogether. The
gate already has the listing that sees both ends of a rename
(`_changed_with_status`, used for the append-only and validity checks); the
scope and lane checks read the other one.

## What Changes

- The gate derives the set of paths a candidate touches from one listing in
  which a rename contributes its source as a deletion and its destination as an
  addition; the scope check, the lane choice and the emptiness check read that
  set.
- A rename out of scope is refused with the source path named among the paths
  outside contract scope; a rename within scope passes as before.
- A move into the journal is a diff-lane candidate, not a journal-only one.
- New capability `scope-enforcement`, stating what the gate holds a candidate's
  paths to.

## Impact

- `src/agentmarshal/journal/gate.py`: the name-only helper goes; every reader of
  the candidate's paths reads the decomposed listing.
- `tests/test_gate.py`: three new scenarios; the 0.3.0 byte-for-byte transcript
  test is unmodified — a candidate without renames lists the same paths.
- No contract, record or CLI change.
