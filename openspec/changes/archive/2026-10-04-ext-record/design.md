## Context

ADR-0013 decision 18 decided extension records are a shared `ext` type: the
core knows the envelope, the kind carries a namespace and a version and is
declared in the manifest, and the body is opaque to the core — hash-pinned
and size-limited. ADR-0022 section 3 gave the record schema 7 and its four
fields, `recorded_by` with `recorded_by_source` required, and no admission
after a terminal record. CR-154 laid down how a record type is declared once
— `RECORD_TYPES` in `attestation.py`, everything else derived or pinned —
and how a field family registers; CR-167 (`check`), CR-170
(`acknowledgement`) and CR-177 (`agreement`) registered the closest
precedents through that mechanism. Neither ADR fixes how `payload_sha256`
is computed; this change fixes the canonical form. The leak scan at write
belongs to the command that writes the record (`record-ext`), as the
`check` excerpt's does to `record-check`; `validate`'s "addressee not
found" warning and the check that a kind is declared by a manifest are
later tasks too.

## Goals

- An `ext` record type exists from schema 7: no projected state, admitted
  after no terminal record, writable, `recorded_by` with
  `recorded_by_source` required.
- Its fields: `kind` (`<name>/<kind>@<version>`, the manifest's own rule),
  `commit` (required, 40 lowercase hex), `payload` (any JSON value,
  canonical form at most 64 KiB) and `payload_sha256` (64 lowercase hex,
  the sha256 of the canonical form).
- An `ext` record on a schema below 7 is refused at write and on read;
  writing one stamps 7.
- `validate` and `status` handle a task carrying one without failing.

## Non-Goals

- The `record-ext` command, the leak scan of the payload at write,
  `validate`'s "addressee not found" warning, checking that a kind is
  declared by a manifest, and any reader of the body — all later tasks.
- Any meaning of the payload: it is opaque to the core (ADR-0013
  decision 18).
- Protection beyond what the published decisions promise — see
  docs/threat-model.md — including against processes of the same OS
  user.

## Decisions

- **The type declares once in `RECORD_TYPES`.** Predicate
  `https://agentmarshal.dev/attestations/ext/v1`, `projects_to=None` — an
  ext record changes no task state — `admitted_after_terminal` empty
  (ADR-0022 section 3: post-gate results go to the process log),
  `writable`, `requires_recorded_by=True`: the record is the claim of
  who, as on `check`, `agreement` and `acknowledgement`, and a recorder
  that is not a declared actor is still accepted. Everything else
  derives: `PREDICATE_TYPES`, the projection's tables, the writable set.
  The two hand-written places a new type still touches get theirs:
  `_RECORD_FIELDS` gains `"ext"`, `WritableRecordType` gains `"ext"`,
  and the pinning tests gain the literals.
- **The ext fields register as a schema-7 field family** — `(7, "ext",
  _SCHEMA_7_EXT_FIELDS)` with `kind`, `commit`, `payload` and
  `payload_sha256`. `_RECORD_FIELDS["ext"]` holds the envelope alone;
  below 7 the family's fields are not admitted, so an ext record
  carrying them is refused at write and, on read, by the field-admission
  rule of the record's own schema.
- **The record-type gate is its own rule bound to 1**, like `check`,
  `agreement` and `acknowledgement`: `ext` refuses `record_type: ext`
  below schema 7 whatever the record carries — it guards admission, not
  history, and no legitimate history can carry the type.
- **`kind` follows the manifest's own rule, imported — never copied.**
  The form `<name>/<kind>@<version>` is `_RECORD_KIND` in
  `extensions.py`, the fullmatch `_parse_record_kinds` applies to every
  `kinds` entry; the record's `kind` answers to the same compiled rule
  so the two cannot drift. The import is deferred to where the rule
  runs: `extensions.py` stands on this module through `contracts.py`
  (`contracts.py` imports `forges_rendered_text`), so a module-level
  import back would cycle — the `accepted_pause` precedent names the
  same cycle and is why the import is deferred rather than top-level.
  Whether a manifest actually declares the kind is the later warning's
  question, not this rule's.
- **`payload_sha256` pins the canonical form — the one the byte bound
  already measures.** The canonical form is the payload's JSON
  serialization with sorted keys, no insignificant whitespace
  (separators `,` and `:`), non-ASCII characters unescaped, encoded as
  UTF-8: `_canonical_json`, the encoding the bounded-JSON rule measures
  on, `allow_nan=False` so a non-finite float has no JSON form and is
  refused naming `payload`. One byte sequence for the bound and the pin:
  the same payload with keys in another order hashes the same, and a
  reader verifying the record recomputes the same digest however the
  file happened to be spaced.
- **`payload` registers `_JSON_BYTE_LIMITS[("ext", "payload")] = 64
  KiB`** — the shared bounded-JSON validator of ADR-0022 section 8,
  which this table has held empty waiting for. The family's own rule,
  `ext-fields-7` bound to 7 like its siblings, checks `kind`'s form,
  `commit`'s 40-lowercase-hex shape, `payload`'s presence and
  `payload_sha256`'s 64-lowercase-hex shape and its equality with the
  sha256 of the canonical form — each refusal naming the field.
- **`kind`, `commit` and `payload_sha256` register into
  `_FORGEABLE_TEXT_FIELDS`** keyed `("ext", field)` — the family's
  displayed strings, `commit`'s and `payload_sha256`'s entries never
  firing as their hex shapes stand first, `kind`'s refusing what the
  form rule admits but a rendered line would not survive (a
  bidirectional mark is not `\s`). `payload` registers nowhere else: it
  is a JSON value, not a displayed string, and the fail-closed
  forgeable-text rule would refuse it as a non-string.
- **`_minimum_schema` raises to 7 on the type** — `record_type ==
  "ext"`, the `check`, `agreement` and `acknowledgement` precedent —
  and `create_ext_record` builds the record through the same one
  derivation, stamping 7. The builder computes `payload_sha256` itself
  over the canonical form, so a caller can never supply a mismatched
  pin; an unencodable payload is refused there naming `payload`, as the
  record rule does.

## Risks

- [A hand-made `ext` record stamped below 7 with none of its fields
  reads] → the `ext` rule bound to 1 refuses the type below its schema,
  and one carrying its fields is refused by `fields` anyway.
- [An `ext` record a candidate adds names no recorder] →
  `requires_recorded_by` makes the recorded-by rule refuse it; the write
  path stamps the pair from the environment before writing.
- [The `kind` rule could drift from the manifest's] → the record imports
  the manifest's own compiled rule; only the import is deferred, never
  the rule copied.
- [A pin computed over the file's spacing could disagree across writers]
  → the canonical form is the one byte sequence the bound already
  measures; writer, bound and reader share it.
- [The registry pinning tests enumerate the types literally] → they are
  updated with the new literals in the same change, so the drift the
  pins exist to catch cannot pass silently.
