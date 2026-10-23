## Context

ADR-0018 decision 2 recorded the governance model: agreement is an
actor's statement that the contract at a stated hash is the one agreed
to — advisory evidence, any declared actor may record it, there are no
roles. ADR-0022 section 3 gave the record its schema-7 shape —
`contract` plus the required `recorded_by`/`recorded_by_source` pair —
and CR-177 landed the record type. CR-163 and CR-179 laid down the two
primitives this command composes: `contract_sha256`, the one hash every
pin uses, and the pin itself — `contract` on `opened` and `amendment`
records, where the latest hash-carrying record is the one compared.

## Goals

- `agentmarshal agree --task <id>` writes one `agreement` record at the
  contract's current hash, printing the hash and the recorder.
- `--contract <hash>` makes the agreement bind the text the actor read:
  the record lands only when the value equals the current hash.
- A contract drifted from its latest pin is refused until `amend`
  records the edit — agreeing with a text no record pins is agreeing
  with something the journal cannot name.
- Tasks opened before contract hashes existed carry no pin and agree at
  the current text.
- Every refusal writes nothing and names its reason.

## Non-Goals

- The gate's `require_agreement` check and `status` showing who agreed —
  later tasks.
- Roles, or any restriction on who may agree (ADR-0018 decision 2).
- Authentication: recorder is provenance, not identity proof — the
  threat model's boundary stands as published.
- Refactoring `status_view`'s drift helper into shared code — the
  command restates the same pin scan over records it already holds;
  growing a public surface in the view module to serve one writer is a
  wider change than the handful of lines restated.

## Decisions

- **One module, `agree.register` + `agree.run`.** The command lives in
  `src/agentmarshal/agree.py` and registers into `cli.py`'s subparsers
  the way `steps` does — the modular-registration pattern, kept for a
  single command rather than a group so the dispatch table stays one
  `if` per module.
- **The hash is the journal repository's `contract.md`, hashed the one
  way.** `contract_sha256(path.read_bytes(), str(path))` — CRLF and LF
  forms of one text hash alike, which is why the pin comparison can be
  exact equality. In a sidecar the journal's copy is the one agreed
  with, the same copy `amend` pins.
- **The pin is restated locally, not imported from the view.** The
  latest `contract` on `opened`/`amendment` records is scanned from the
  records `load_task_for_record` already returns — three lines over data
  in hand. `status_view._contract_drift_line` renders a line for a
  reader; the command needs the pin for a refusal, and reaching into the
  view's private helper would couple a writer to a renderer's internals.
- **Refusal order is: argument shape, task eligibility, readability and
  drift, explicit-hash equality, recorder.** `--contract` that is not 64
  lowercase hex is refused before the journal is touched — a mistyped
  flag fails cheap. Lifecycle eligibility goes through
  `load_task_for_record(..., "agreement")`, the same projection gate
  every writer answers to, so a completed or abandoned task is refused
  naming its state. The explicit-hash comparison runs before the
  recorder check so a hash the actor mis-transcribed is refused on the
  hash, not the identity. The recorder resolves last — an agreement with
  no recorder is a record the schema refuses, so the command decides it
  before `write_record` can create the records directory; a recorder who
  is not a declared actor is written, with a stderr note saying so.
- **Drift outranks `--contract`.** A drifted contract is refused even
  when `--contract` equals the old pin: the pin names a text that is no
  longer current, and agreement with it is agreement with a stale text.
  The refusal names both short hashes and `amend`, the way `status`
  words the same fact.
- **Output names what it must and escapes what it must.** The record
  path, the hash and the recorder print on stdout; refusals and the
  undeclared-actor note print on stderr. The recorder passes through
  `escape_for_display` — the only untrusted text the command renders —
  so a name carrying line-forging bytes cannot fabricate transcript
  lines. The hash needs no escaping: its shape is 64 lowercase hex by
  construction.
