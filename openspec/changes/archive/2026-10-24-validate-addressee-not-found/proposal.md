## Why

[ADR-0013](../../../../docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
decision 18 decided `validate` checks the `ext` envelope — and that a
`kind` no manifest declares draws a warning, "addressee not found", not
a refusal, because a record can outlive the manifest that declared its
kind. CR-179 landed the record, CR-212 the command that writes it only
for a declared kind, CR-152 the `[records].kinds` declaration. What does
not exist yet is the read side: today `agentmarshal validate` reports an
`ext` record like any other, and a reader of the journal cannot see that
the extension that would interpret it is gone.

## What Changes

- `validate` checks every `ext` record's `kind` against the
  `[records].kinds` shared extension manifests declare in the working
  tree — the `<name>` segment of the kind names the extension, whose
  manifest is read through `read_extension_manifest` in the file form
  or the directory form, the same lookup `record-ext` makes. A kind no
  manifest declares draws one `WARN` line naming the task, the record
  id and the kind, worded "addressee not found". The warning changes
  nothing else: not the passed/failed verdict, not the exit status.
- A manifest that cannot be read is named once on a `WARN` line of its
  own, however many records name the extension, and its kinds count as
  undeclared; a missing manifest draws no line of its own — the
  addressee warning is its report.
- A journal holding no `ext` record reads no manifest and prints
  exactly what it prints today.

## Capabilities

- modified: `extension-records`

## Impact

One new helper in `validate.py`; no other command changes, and the gate
— which reads neither `validate`'s output nor any `WARN` line — is
untouched. The warning makes `validate` another reader of manifests,
after `brief`, the gate and `doctor`, where ADR-0010 decision 4 counted
two. The `ext` record's body stays opaque: the check reads the envelope
and the manifest declarations, never the payload.
