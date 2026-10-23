## Why

[ADR-0013](../../../../docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
extends
[ADR-0007](../../../../docs/adr/ADR-0007-operator-acceptance.md)'s operator
acceptance twice: a pause raises no review finding, so its acceptance
stands over the pause itself (decision 5), and an operational CR carries
no review at all, so an adopter who requires acceptance for it accepts
the CR, not a verdict (decision 17).
[ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 2 gives the record the fields — `accepted_pause: {extension}`
and `operational: true`, each bound by `accepted_commit` — and CR-173
landed them in the record model, the readers and
`create_acceptance_record`. What does not exist is the writing path:
`agentmarshal accept` can record an acceptance over findings only, so an
operator who must accept a pause or an operational CR has no command
that carries the decision onto the journal.

## What Changes

- `accept` gains two form flags: `--pause <extension>` writes an
  acceptance carrying `accepted_pause` for that extension, and
  `--operational` writes one carrying `operational: true` — each through
  `create_acceptance_record`'s existing parameters, bound by
  `accepted_commit` to the commit `--commit` resolves to in the
  journal's repository, with no `findings` and no review consulted.
- `--pause` accepts only an extension the journal repository's working
  tree declares as a shared extension — the manifest read through
  `read_extension_manifest` in either form — and refuses naming the
  extension otherwise.
- The three forms are mutually exclusive and exactly one is required:
  `--pause` and `--operational` refuse each other, and `--finding` and
  `--accepted-finding` are refused with either, each refusal naming the
  flags. Acceptance over findings is unchanged.
- Every refusal writes nothing; the gate, which reads no pause or
  operational acceptance yet, is unchanged.

## Capabilities

- modified: `operator-acceptance`

## Impact

One command's parser and one trusted-path function: `cli.py`'s `accept`
parser and dispatch, and `acceptance.py` beside `accept_findings`. No
other command changes, and every output for an acceptance carrying
`findings` stays byte for byte what it was. Neither new form is read by
the gate — the lanes that consume these acceptances are later tasks —
so nothing here weakens the merge decision.
