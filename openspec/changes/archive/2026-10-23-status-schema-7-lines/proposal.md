## Why

CR-167, CR-170, CR-177 and CR-179 landed the `check`, `acknowledgement`,
`agreement` and `ext` records; `status` falls back to the generic id, type
and time line for each. The decisions pair every one of these records with
visibility: ADR-0021 decisions 4 and 5 — `status` shows who acknowledged
and marks a self-acknowledgement; ADR-0018 decision 2 — the absence of an
agreement is shown, instead of being indistinguishable from agreement
never asked for, and `status` shows who agreed; ADR-0022 section 3 — a
recorder that is not a declared actor is shown as such.

## What Changes

- `status <task>` renders one line of its own per `check` (name, result,
  short commit, failed step when present), `agreement` (short contract
  hash and who agreed), `acknowledgement` (short commit, the file as
  recorded, the signature or the marker's number, who acknowledged and
  the reason) and `ext` (kind, short commit, short payload hash) record,
  through the renderer registry the other record types already use.
- Each of the four lines names the recorder; a recorder that is not a
  declared actor is shown as not a declared actor (ADR-0022 section 3).
- An acknowledgement whose recorder is a declared author or committer of
  the acknowledged commit is marked self-acknowledged, derived on display
  the way self-acceptance is and never stored; where git cannot read the
  commit the line says the mark was not checked (ADR-0021 decision 5).
- After the record lines `status <task>` prints one line when no
  agreement is recorded, and one line naming both short hashes when the
  latest agreement's hash differs from the contract's current hash —
  compared against the current hash, not the pin (ADR-0018 decision 2).
  Neither line fails the command or changes the task's state.
- Every value taken from a record is escaped on display as the other
  lines are; apart from the agreement line, the output of every other
  record type, the header, the drift line, the overdue-step and path
  output is unchanged byte for byte.

## Capabilities

- modified: `review-evidence`, `contract-governance`, `leak-scan`,
  `extension-records`

## Impact

`status_view.py`'s `RecordRenderer` gains the journal root — renderers
that check the recorder against the project file's `actors` table need
the journal's own project, not the invoking checkout's. The dispatch
still escapes what a renderer returns, so a renderer cannot forget to
(ADR-0015 decision 5). No record schema, no reader, no command besides
`status` changes; the `status` list form is unchanged.
