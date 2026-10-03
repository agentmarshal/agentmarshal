## Context

`open_task.open_task` writes the contract template and the `opened`
record in one staged transaction; `_run_amend` in `cli.py` builds the
`amendment`; `migrate._migrate_task` writes each migrated contract and
its records; `status_view.print_task_detail` renders the per-task
`status` view. CR-163 left `create_opened_record` and
`create_amendment_record` with the optional `contract` argument and
`contract_sha256` as the one way any place hashes a contract
(contract-governance's own requirement). This is the transition task
that proposal announced: the writers set the field.

## Goals

- Every contract a writer establishes is pinned by its `contract_sha256`.
- `open` accepts a contract written first, so the pinned hash is real,
  not a template's.
- A drift between the contract and its last pin is visible in `status`.

## Non-Goals

- Any gate or `validate` check of the hash or of agreement (later tasks).
- Recomputing hashes in existing records.
- `brief` or `report` display of the hash.
- The `agreement` record type — its own task.

## Decisions

- **The pin covers the exact text written, computed one way.** `open`
  hashes the UTF-8 encoding of the contract text it stages — the
  template, or the provided file with its `id` retargeted — the same
  bytes the write lands. `amend` and `migrate` hash the contract file's
  bytes on disk. Every place calls `contract_sha256`; no second way.
- **`--contract-file` rewrites only the `id` line.** The task id is
  assigned inside `open_task`, so the retarget happens there: the header
  line that declares `id` — written as the key `id`, `"id"` or `'id'`
  with a one-line string value on a line of its own — is replaced, and
  every other byte is kept, line endings and a byte-order mark included.
  A look-alike line is not the declaration: the same text inside a
  multi-line string value or under a `[table]` header matches the
  pattern, so a candidate is confirmed by rewriting it and re-parsing —
  only the line whose rewrite changes the parsed `id` is retargeted, and
  the rewritten text is parsed again as a confirmation that it still
  names a contract whose header parses and that the `id` now is the
  task's. A valid contract whose `id` is written another way — an
  escaped key, a value spanning lines — is refused with a message naming
  the supported forms. A different value is carried on
  `OpenedTask.replaced_id` for the CLI to name on stderr.
- **The provided contract is validated before the journal is touched.**
  `_read_provided_contract` reads, decodes and validates the file ahead
  of every directory `open` creates — the header's parse, and that its
  `id` sits where the rewrite reaches it — so a file that is missing,
  unreadable, not a valid contract or one whose `id` is written another
  way is refused with nothing written — the same boundary
  `parse_contract_text` is for a contract already in the journal.
- **`amend` refuses through the load it already does.**
  `load_task_for_record` parses the contract, so a `contract.md` that
  does not parse is refused before the hash is read and no record is
  written. The path hashed is the journal's `tasks/<id>/contract.md` —
  the journal repository's copy, which in a sidecar is where the contract
  is versioned (ADR-0008).
- **The drift line compares against the latest hash-carrying record.**
  `print_task_detail` takes the journal root, scans the records it
  already holds for the newest `contract` on an `opened` or `amendment`
  record, hashes the contract file and prints one line — naming the
  pinned and the current short hashes and that the edit should be
  recorded with `amend` — when they differ. A task with no hash-carrying
  record, a matching hash, or a contract that cannot be read prints
  nothing: the line is a reminder, never a failure.
- **The published "may carry" requirement is restated, not weakened.**
  The field stays optional in the record model — records written before
  it existed keep validating — but "the field is optional" no longer
  describes anything the tool's writers do: every command that
  establishes a contract now pins it. The requirement is modified to say
  the optionality is the model's, not the writers'.

## Published requirements checked and left alone

- The hash requirement's one function serves the new writers unchanged:
  `contract_sha256` over the bytes as stored or read.
- "The contract field is refused below schema 7" is untouched: a record
  carrying none of the family still stamps the schema it stamps without
  it, which the record-layer tests keep demonstrating.
