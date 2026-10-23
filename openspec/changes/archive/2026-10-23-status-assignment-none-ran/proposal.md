## Why

CR-191's review left an advisory finding, deferred: in the declared
assignment `status` prints the declaration and, when no implementer
session or review has been recorded, nothing on the side of what ran —
while the section's own rule says an absence is stated rather than
omitted, and the scope section prints `(none)` in the same situation. A
declared assignment with a silent ran side reads as though the side
were not there at all.

## What Changes

- When the contract declares `implementers` and no implementer session
  is recorded, the assignment section prints
  `- implementer sessions: (none)` where the session lines would stand;
  when it declares `reviewers` and no review is recorded,
  `- reviews: (none)` where the review lines would stand — the scope
  section's `(none)` for an empty ran side.
- A ran side whose list the header does not declare prints no `(none)`
  line: `(not declared)` already states that side has no assignment.
- Nothing else `status` prints changes — the record lines, the
  agreement and drift lines, the overdue-step and path lines — and no
  other command changes.

## Capabilities

- modified: `contract-governance`

## Impact

`_assignment_lines` in `status_view.py` gains the two `(none)` lines;
the record renderers, the record model and every other command are
unchanged. A contract declaring none of the three fields keeps the
detail view byte for byte, and the byte-for-byte pins of the section
keep holding.
