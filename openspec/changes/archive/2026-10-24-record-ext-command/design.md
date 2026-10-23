## Context

ADR-0013 decision 18 fixed what an `ext` record is and who may write one:
extension records are a shared `ext` type — the core knows the envelope,
the kind carries a namespace and a version declared in the extension's
manifest, the body is opaque to the core, hash-pinned and size-limited —
and only a shared extension writes `ext`, never to the journal directly:
the record goes through the core's command. ADR-0022 section 3 gave the
record its fields — `kind`, `commit` (required), `payload` (JSON, up to
64 KiB, leak-scanned at write), `payload_sha256` — `recorded_by` with
`recorded_by_source` required, and no admission after a terminal record:
post-gate results go to the process log. Section 8 bounded the canonical
form at 64 KiB.

The pieces this command composes all exist: `create_ext_record` builds
the record and computes `payload_sha256` over the canonical form
`_canonical_json` produces — the one byte sequence the bounded-JSON rule
measures (CR-179); `load_task_for_record` answers lifecycle admission;
`read_extension_manifest` reads a manifest in either form with its
symlink rules and exposes `record_kinds` (CR-152); `mask_leaks` beside
`scan_for_leaks` in `capture.py` is the masking the `check` excerpt uses
(CR-183), and `markers_from_config` reads the project's private markers
from the working tree; `_project_root_for` + `resolve_recorded_by` and
`_declared_actor` are the recorder resolution and note `record-check`
already runs.

## Goals

- `agentmarshal record-ext --task <id> --commit <rev> --kind
  <name>/<kind>@<version> --payload-file <path>` writes one `ext` record:
  the commit resolved to its full 40-hex id, the payload read as JSON and
  masked, the hash computed over the masked payload's canonical form.
- The kind lands only when the shared extension `<name>`'s manifest in
  the working tree declares it in `[records].kinds`.
- Every refusal writes nothing and names its reason; a recorder that is
  not a declared actor is accepted and named as such.

## Non-Goals

- Reading or interpreting the payload — it is opaque to the core; no
  command reads the body yet.
- `validate`'s "addressee not found" warning — a later task; this
  change's manifest check is the write-side gate, not the read-side
  warning.
- Running extensions, and personal extensions writing records — they
  have no authority (ADR-0013 decision 15).
- Protection beyond what the published decisions promise — see
  docs/threat-model.md — including against processes of the same OS
  user.

## Decisions

- **One module, `record_ext.register` + `record_ext.run`.** The command
  lives in `src/agentmarshal/record_ext.py` and registers into `cli.py`'s
  subparsers the way `steps`, `agree`, `acknowledge` and `record-check`
  do — one import, one `register` line, one dispatch `if`.
- **The commit is resolved in the journal's repository.** `git rev-parse
  --verify <rev>^{commit}` under `placement.project_root` — the
  repository that holds the journal in either placement, the same rule
  `record-check` applies: a sidecar records against the commits its own
  repository carries, and the host's are never asked. What resolves to
  no commit is refused naming the reference, before anything is written.
- **The manifest is the shared scope's declaration.** `<name>` is the
  first segment of `--kind`; `read_extension_manifest` reads
  `.agentmarshal/extensions/<name>.toml` or
  `.agentmarshal/extensions/<name>/manifest.toml` from the journal
  repository's working tree — either form, with its symlink rules — and
  the write proceeds only when the kind occurs in the manifest's
  `record_kinds` exactly as given. A `--kind` that fails the manifest's
  own form rule is refused before the manifest is read; a missing or
  unreadable manifest and an undeclared kind each refuse naming the
  kind — a malformed manifest's error rides along, escaped. There is no
  second reader and no second form rule: `_RECORD_KIND` is imported, not
  copied.
- **The scan is the project's own, over every string the payload
  carries.** `markers_from_config` on the journal repository's working
  config — the same read `record-check` makes — then each string in the
  parsed payload, object keys included, is passed through `mask_leaks`
  at any depth: each matched span becomes `[masked: <category>]` and the
  command names the categories on stderr, never the matched text and
  never a marker's value. Masking keys, not just values, is what keeps a
  secret used as an object's member name out of the record; two keys
  that mask to one are refused, since the collapse would silently drop a
  member. The canonical form of the masked payload is scanned once more:
  a marker occurring in the mask label itself, or spanning a boundary no
  single string holds, still trips it, and then the write is refused
  naming the categories — unlike `record-check`'s withheld excerpt there
  is nothing smaller to keep, the payload is the record. A masked
  canonical form past 64 KiB is refused the same way.
- **The hash covers what the record carries.** `create_ext_record`
  computes `payload_sha256` over the canonical form of the payload it is
  handed — the masked one — so the pin is over what the journal holds,
  never over the file as given; a file that does not parse as JSON, or
  cannot be read, is refused naming it, and a payload with no JSON form
  — a non-finite number a lenient parse admits — is refused naming
  `payload` where the builder's own refusal stands.
- **Refusal order: task, commit, kind, payload, recorder, record.**
  `load_task_for_record(..., "ext")` answers lifecycle admission — an
  unknown task refused naming it, a completed or abandoned task refused
  naming its state, an ext record admitted after no terminal record. The
  recorder resolves through `resolve_recorded_by` and the record passes
  `validate_record_for_write` before `write_record` — shape, the kind's
  forgeable-text rule, the bound — so only a writable record reaches the
  journal, and every refusal leaves it byte-identical.
- **Output names what it must and escapes what it must.** The record
  path, the resolved commit, the kind and the recorder print on stdout;
  refusals, the masked-categories note and the undeclared-actor note
  print on stderr. The recorder and values the tool did not write pass
  through `escape_for_display`; a kind that reached the write already
  passed the manifest's own control-character rule.

## Risks

- [A second kind-form rule or manifest reader drifting from the
  manifest's] → there is none: `_RECORD_KIND` is imported and
  `read_extension_manifest` is the one filesystem reader, so the form
  check and the forms admitted cannot drift.
- [A secret in a key surviving the value-only masking] → keys are
  masked with the values; a secret can hide anywhere in the payload and
  every string is covered.
- [The mask label echoing what it hides] → the rescan of the canonical
  form catches a marker occurring in the label or across a JSON
  boundary, and the write is refused with the categories named and the
  matched text nowhere.
- [A refusal writing something anyway] → every check runs before
  `write_record`; the refusal tests snapshot the journal and run
  `validate`.
- [A matched span printed while naming it] → only categories print;
  the tests assert the matched text appears in neither stdout, stderr,
  nor the record.
