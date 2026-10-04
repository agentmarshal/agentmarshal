## Context

ADR-0007's acceptance is over findings: an operator accepts a commit over
exactly the blocking findings its latest non-approving review raised.
ADR-0013 decision 5 extends it to an extension pause — which raises no
review finding — and decision 17 to an operational CR — which carries no
review at all. ADR-0022 section 2 names the fields: `accepted_pause:
{extension}` and `operational: true`, each bound by `accepted_commit`, in
schema 7.

CR-154 laid down how a field family registers — a `_FIELD_FAMILIES` entry
plus the shared validator tables keyed by (record type, field) — and CR-170
registered the `acknowledgement` type's family through it; the contract-hash
change registered a field family on an existing record type the same way.
The acceptance readers today are three: the gate's two lanes, each of which
takes the latest acceptance on its binding and reads `findings`
unconditionally; `status`, whose summary line and record line assume
`findings`; and `report`, which derives `accepted-over-findings` from any
acceptance record at all.

## Goals

- From schema 7 an `acceptance` record carries exactly one of `findings`,
  `accepted_pause` and `operational`; the new forms bind by
  `accepted_commit` only.
- Every reader treats a pause or operational acceptance as not an
  acceptance over findings: the gate judges by the latest acceptance
  carrying `findings` on either binding, `status` renders the new forms,
  and `report` derives `accepted-over-findings` from a findings acceptance
  alone.
- Every output for an acceptance carrying `findings` is unchanged byte for
  byte.

## Non-Goals

- The commands that write the new forms (`accept --pause`, `accept
  --operational`), extension stages and pauses themselves, the operational
  lane, and any gate or `complete` behaviour acting on a pause or an
  operational acceptance — later tasks.
- Any change to ADR-0007's rules for an acceptance over findings beyond
  keeping them to the acceptances that carry `findings`.
- `extensions.py`'s `_validate_name` — the extension-name rule is
  replicated, not imported: `extensions.py` stands on `records.py`, and an
  import back would cycle.

## Decisions

- **The new fields are a schema-7 field family on `acceptance`** — `(7,
  "acceptance", _SCHEMA_7_ACCEPTANCE_FIELDS)` — the registration the
  contract-hash and acknowledgement families used, not a second mechanism.
  `_RECORD_FIELDS["acceptance"]` keeps `findings`, the pre-7 form's field;
  below 7 the family's fields are not admitted, so an acceptance carrying
  one is refused at write and, on read, by the field-admission rule of the
  record's own schema. `_minimum_schema` raises to 7 on the family's
  fields, the way it does on the other field families; an acceptance
  carrying `findings` stamps what it stamped.
- **`_validate_acceptance_record` requires exactly one of the three
  forms**, the refusal naming `findings`, `accepted_pause` and
  `operational` — the generalization of the `_validate_binding` phrasing
  for the exactly-one pair. The rule keeps its schema-1 binding: a record
  of an earlier schema without `findings` must still be refused on read,
  and no legitimate history carries the new fields below 7 — the `fields`
  rule refuses those first, at write and on read. The `findings`
  validation itself is unchanged and runs when the record carries
  `findings`; `accepted_by` and `reason` stay required for every form.
- **The family's own shape rule, `acceptance-fields-7`, is bound to 7**
  like `session-fields-7`, `check-fields-7` and `acknowledgement-fields-7`.
  It refuses a new form bound by `accepted_finding` (both forms bind
  `accepted_commit` — ADR-0022 section 2), an `accepted_pause` that is not
  an object carrying exactly `extension`, an `extension` that is not a
  string, is empty, is not one path component (not `.`, not `..`, no `/`
  or `\` — the rule `_validate_name` applies to an extension name,
  replicated in `records.py`'s terms), or carries a character that could
  forge a line, and an `operational` that is not `true`. The family
  registers nothing in the validator tables: `accepted_pause`'s value is
  an object, not a displayed string, so the extension name it carries gets
  the same `_reject_control_characters` check the finding ids get inline;
  ADR-0022 section 8 bounds `excerpt`, `payload` and the new record types'
  `reason` alone, so no limit table gains an entry.
- **`create_acceptance_record` gains keyword-only `accepted_pause` and
  `operational`** — the extension whose pause is accepted, and the flag —
  beside `findings`, which the new forms pass as `None`; the record carries
  `accepted_pause: {"extension": <name>}` or `operational: true`. The
  builder refuses more or fewer than one form and a new form bound by
  `accepted_finding` up front, the same refusal `create_review_record`
  gives its own pair.
- **The gate filters to the acceptances carrying `findings` on both
  bindings.** On the commit binding the filter is load-bearing: "the
  latest acceptance, judged as it stands" becomes the latest acceptance
  *over findings*, so a pause or operational acceptance written later
  cannot shadow one. On the finding binding the `accepted_finding` match
  already excludes the new forms for any record the validators saw; the
  filter is the same rule stated explicitly, so a record handed to the
  gate without validation — the in-memory path the gate's own tests use —
  is judged no differently.
- **`status` renders the new forms where the findings form names its
  findings**: `accepted_pause=<extension>` or `operational` in the record
  line, "accepted pause of extension `<name>`" or "accepted operational CR"
  in the summary line, with the binding rendered as it is for a commit
  acceptance and the self-acceptance marking unchanged — the new forms
  always bind `accepted_commit`, so `_is_self_accepted` answers them the
  same way. `report` derives `accepted-over-findings` only from an
  acceptance carrying `findings`; nothing else reads the new fields.

## Risks

- [A hand-made acceptance stamped below 7 carrying a new field] → the
  `fields` rule refuses it at write and on read, the field-admission rule
  of the record's own schema; no new gate is needed because the type
  itself predates schema 7.
- [A pause acceptance recorded after a findings acceptance on the same
  commit] → the gate judges the latest acceptance carrying `findings`;
  `status` shows the pause for what it is.
- [An acceptance without `findings` reaching a reader] → the only places
  that read `findings` unconditionally were the gate's two lanes and the
  `status` record line; all three are guarded, and `report` only tests the
  field's presence.
