## Why

ADR-0018 decision 3 lets a schema-3 contract name the permitted
implementers and reviewers — ordered as the fallback order — and the
independence rules in force; CR-147 landed the header fields and CR-186
made the gate judge the declared rules at the merge boundary. Nothing
shows the declaration to a reader yet: the lists and the rules sit in
the contract, and who actually implemented and reviewed sits in the
records, with no surface putting the two side by side. The same decision
pairs them: `status` shows the declared assignment next to what actually
ran, and the reason for a fallback is shown, not verified.

## What Changes

- `status <task>` prints an assignment section after the scope and
  before the record lines when the contract header declares any of
  `implementers`, `reviewers` and `independence`: the declared lists in
  their declared order and the declared rules, each on a line of its
  own, a field the header does not declare shown as not declared.
- Next to the declaration the section shows what ran: one line per
  implementer session — a session record whose `role` is `implementer`
  — carrying its `actor`, the vendor from `usage.provider`, its `model`
  and its `fallback_reason` when the record carries one; one line per
  review carrying its reviewer's `actor`, `vendor` and `model`. An
  absent value is shown as absent, never derived from another field.
- An actor that ran but is not in the declared list is marked
  `(not declared for the role)` — shown, not refused — and the mark
  appears only when the contract declares that role's list (ADR-0018
  decision 3).
- A contract declaring none of the three prints exactly today's detail
  view; every value the section takes from a contract or a record is
  escaped on display.

## Capabilities

- modified: `contract-governance`

## Impact

`status_view.py` gains the section inside `print_task_detail`, between
the scope block and the record lines; the renderer registry, the record
model and every other command are unchanged. The gate's fixtures and
every documented transcript a test pins stay byte for byte.
