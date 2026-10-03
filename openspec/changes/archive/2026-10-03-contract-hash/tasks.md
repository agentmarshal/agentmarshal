## 1. One way to hash a contract

- [x] 1.1 `contract_sha256` in `contracts.py` takes a contract's bytes,
  decodes them as UTF-8, translates CRLF and lone CR to LF as Python's
  text reading does, keeps a byte-order mark, and returns the lowercase
  hex sha256 of the result encoded as UTF-8; undecodable bytes are
  refused naming the source — verify: LF equals CRLF and lone-CR hashes;
  BOM kept; bad bytes refused naming the source (pytest).
- [x] 1.2 The review launcher computes `reviewed_contract` with it —
  verify: a test computes it both ways on LF, CRLF and BOM-bearing
  inputs and the values match (pytest).

## 2. The contract field

- [x] 2.1 `_SCHEMA_7_CONTRACT_FIELDS` and the `_FIELD_FAMILIES` entries
  `(7, "opened", …)` and `(7, "amendment", …)` admit `contract` from
  schema 7 — verify: a schema-7 record carrying it round-trips; below 7
  refused (pytest).
- [x] 2.2 `("opened", "contract")` and `("amendment", "contract")`
  register into `_FORGEABLE_TEXT_FIELDS` — the entry never fires, the
  hex shape admitting nothing the rule refuses — and no entry lands in
  the length-bound tables — verify: a forgeable character refused; a
  long value is not the concern, the shape bound is (pytest).
- [x] 2.3 The `contract-hash-7` rule, bound to 7, refuses a `contract`
  that is not exactly 64 lowercase hex — verify: pytest, and the
  rule-table test gains the binding.
- [x] 2.4 `_minimum_schema` raises to 7 on `contract` and
  `create_opened_record` and `create_amendment_record` accept it as an
  optional keyword argument — verify: the minimum-schema parametrization
  gains the field cases (pytest).

## 3. Nothing that worked changed

- [x] 3.1 A record without `contract` stamps what it stamps today; no
  writer passes the argument; the gate's fixtures are unchanged —
  verify: `test_journal.py`, `test_record_schema.py` and the gate tests
  stay green.
- [x] 3.2 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
