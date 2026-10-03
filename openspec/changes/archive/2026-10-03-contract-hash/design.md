## Context

The review launcher computes `reviewed_contract` as
`hashlib.sha256(contract.encode("utf-8")).hexdigest()` over text read
with `read_text(encoding="utf-8")` — universal newlines, so a contract
checked out with CRLF endings hashes to the LF value. The gate reads the
contract as raw `git show` output, where no translation happened. One
function must serve both, and the transition task's writers (`open`,
`amend`, `migrate`) hash the bytes they write. CR-154 laid down how a
field family registers and CR-160 registered the session family through
it; this change registers ADR-0022 section 2's `contract` field the same
way.

## Goals

- One function, `contract_sha256` in `contracts.py`, computes a
  contract's hash from its bytes wherever they were read.
- The launcher's `reviewed_contract` is unchanged for every contract it
  reads today.
- `opened` and `amendment` may carry `contract` from schema 7, and a
  record carrying it stamps 7 through the one derivation.

## Non-Goals

- Writing the field from `open`, `amend` or `migrate` — the transition
  task.
- Any gate or status reading of the field.
- Recomputing hashes in existing records.
- The `agreement` record type's `contract` field — a new type, its own
  task.

## Decisions

- **`contract_sha256(content: bytes, source: str)` takes bytes, not
  text.** The places that hash a contract hold different forms: the
  launcher holds decoded text whose re-encoding is the identity for
  hashing, the gate holds raw `git show` bytes, and the transition task's
  writers hold the bytes they write. Bytes are the one form every caller
  can supply without a translation of its own, so the function decodes
  them as UTF-8 — the encoding every contract path already enforces — and
  the refusal names *source*, following `parse_contract_text`'s
  convention of naming the origin (a path or a git object reference) for
  error messages only.
- **The hash is of the text, not the bytes.** The function translates
  CRLF and lone CR to LF after decoding — what `open(newline=None)`'s
  universal-newline mode does, which is how `read_text(encoding="utf-8")`
  reads — and a byte-order mark stays in the hashed text because
  `read_text` keeps it (`utf-8`, not `utf-8-sig`). Hashing the bytes
  instead would give a CRLF checkout a different hash than the same
  contract with LF, and would change `reviewed_contract` on every record
  the launcher writes.
- **The launcher keeps reading text and passes its UTF-8 encoding.**
  The contract the prompt carries is a `str` that `read_text` already
  newline-normalized, so `contract_sha256(contract.encode("utf-8"),
  source)` decodes back to the identical text and the digest is the value
  `hashlib.sha256(contract.encode("utf-8")).hexdigest()` computed before
  — a test computes it both ways over LF, CRLF and BOM-bearing inputs.
  The digest is over the contract text the prompt carries, before any
  escaping for display: the prompt inserts the contract block raw and
  `escape_for_display` touches the named material placed into lines, not
  the contract. review-evidence's "sha256 of the exact contract bytes
  the prompt carried" therefore stays true and the requirement is
  unmodified.
- **The family is two `_FIELD_FAMILIES` entries over one frozenset** —
  `(7, "opened", _SCHEMA_7_CONTRACT_FIELDS)` and
  `(7, "amendment", _SCHEMA_7_CONTRACT_FIELDS)` — the registry keying on
  one record type per entry. A `None` "every type" entry would admit
  `contract` on `review`, `acceptance` and the rest, which the ADR does
  not say. Below 7 the `fields` rule refuses it at write and, on read,
  under the record's own schema — the same field-admission rule that
  gates `usage` from 2 and `reviewed_contract` from 5.
- **`contract` registers into `_FORGEABLE_TEXT_FIELDS` keyed
  `("opened", "contract")` and `("amendment", "contract")`; no length
  table gains an entry.** ADR-0022 section 8 puts every displayed string
  the new fields introduce under the forgeable-text rule, and `contract`
  is displayed — `brief` and `report` will print it. As with `commit`,
  the entry never fires: the 64-lowercase-hex shape rule runs first and
  admits no character the rule refuses. The ADR bounds `excerpt`,
  `payload` and the new record types' `reason` alone, so
  `_TEXT_CHAR_LIMITS`, `_TEXT_BYTE_LIMITS` and `_JSON_BYTE_LIMITS` stay
  empty of the family.
- **One shape rule of the family's own, `contract-hash-7`, bound to
  7.** The 64-lowercase-hex shape — `_SHA256_HEX_PATTERN`, the pattern
  `reviewed_contract` and artifact hashes already measure by — is none
  of the four shared validators, so per the rule-table requirement it is
  a table entry of its own bound to the schema the family registers
  under, sitting with `session-fields-7` ahead of the shared validators.
  It checks `contract` whenever the field is present; a wrong-type
  placement never reaches it, the `fields` rule refusing first.
- **`_minimum_schema` gains one clause** — `record.keys() &
  _SCHEMA_7_CONTRACT_FIELDS` raises the stamp to 7 — beside the schema-4,
  schema-5 and schema-7-session clauses it already holds.
- **`create_opened_record` and `create_amendment_record` accept
  `contract` as an optional keyword argument**, setting the field only
  when supplied — the `usage` and session-family pattern — so a record
  without it is byte-identical to today's. No caller passes it: `open`,
  `amend` and `migrate` writing the hash is the transition task.

## Published requirements checked and left alone

- review-evidence's `reviewed_contract` requirement stays true: the
  function returns the identical digest on the text the launcher reads,
  pinned by the both-ways test.
- record-schema's rule-table requirement already enumerates "the schema-7
  field families' own shape rules" bound to 7 — `contract-hash-7` is one
  — and its minimum-schema and schema-7 requirements speak of "a field a
  schema-7 family admits", which `contract` now is. Its scenario titles
  keep their names.
- session-activity's coordination-schema requirement names the session
  family only; `opened` and `amendment` are not sessions.
- record-lifecycle and contract-history say nothing about these records'
  field sets; contract-governance's header-schema requirements are
  untouched.

## Risks

- [A record stamped below 7 hand-edited to carry `contract` reads fine] →
  it does not: the `fields` rule is bound to 1 and computes the admitted
  set from the record's own schema, so the record is refused on read
  exactly as a schema-1 record carrying `usage` is today.
- [A reader predating schema 7 meets such a record] → intended by
  ADR-0022's upgrade rule: the schema check refuses the record, not a
  field it cannot read.
