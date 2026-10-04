## Why

[ADR-0013](../../../../docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md)
extends
[ADR-0007](../../../../docs/adr/ADR-0007-operator-acceptance.md)'s operator
acceptance twice: an extension pause raises no review finding, so its
acceptance stands over the pause itself (decision 5), and an operational CR
carries no review at all, so an adopter who requires acceptance for it accepts
the CR, not a verdict (decision 17).
[ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 2 gives the `acceptance` record the two forms in schema 7 —
`accepted_pause: {extension}` and `operational: true`, each bound by
`accepted_commit`. Today an acceptance must carry `findings`, and every
reader — the gate on both bindings, `status`, `report` — reads `findings`
off whichever acceptance is latest on the binding. A pause acceptance
written after an acceptance over findings would shadow it, and one without
`findings` would fail the readers outright.

## What Changes

- From schema 7 an `acceptance` record may carry, in place of `findings`,
  `accepted_pause` — an object carrying exactly `extension`, whose value is
  a non-empty extension name that is one path component and passes the
  forgeable-text rule — or `operational` with the value `true`. A record
  carrying more or fewer than exactly one of the three is refused with a
  message naming the three; the new forms bind by `accepted_commit` only and
  are refused with `accepted_finding`; `accepted_by` and `reason` stay
  required.
- The fields register as a schema-7 field family of the `acceptance` record
  type: below 7 they are refused at write and on read, a writer stamps 7
  through the minimum-schema derivation, and `create_acceptance_record`
  builds the new forms.
- The gate, on both bindings, judges acceptance over findings by the latest
  acceptance of that commit or finding that carries `findings`; `status`
  renders each new form naming `accepted_pause=<extension>` or `operational`
  where an acceptance over findings names its findings, with the same
  binding and self-acceptance marking; `report` derives
  `accepted-over-findings` only from an acceptance carrying `findings`.

## Capabilities

- new: `operator-acceptance`

## Impact

Every output for an acceptance carrying `findings` is unchanged byte for
byte — the gate fixtures, the quickstart transcript and the pinned status
view. A pause or operational acceptance changes no gate verdict today: the
commands that write the new forms, the stages, the pauses and the
operational lane that act on them are later tasks, and neither form is a
bypass of the gate.
