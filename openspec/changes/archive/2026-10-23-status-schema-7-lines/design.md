## Context

`status_view.py` renders each record through `_RECORD_RENDERERS`, a
registry keyed on `record_type`; a record type without an entry falls
back to the generic id, type and time line. The four schema-7 record
types — `check` (review-evidence), `agreement` (contract-governance),
`acknowledgement` (leak-scan), `ext` (extension-records) — render through
the fallback today. The published decisions pair each with visibility:
ADR-0021 decisions 4 and 5 (`status` shows who acknowledged, and marks a
self-acknowledgement derived the way ADR-0007's self-acceptance is),
ADR-0018 decision 2 (the absence of an agreement is shown, and `status`
shows who agreed), ADR-0022 section 3 (a recorder that is not a declared
actor is shown as such).

## Goals

- One line per `check`, `agreement`, `acknowledgement` and `ext` record,
  each naming the recorder — and naming a recorder that is not a declared
  actor as such.
- The self-acknowledgement mark derived on display through the same
  author/committer query `_is_self_accepted` runs, saying the mark was
  not checked where git cannot read the commit; nothing is stored.
- One line after the records when no agreement is recorded, and one
  naming both short hashes when the latest agreement's hash differs from
  the contract's current hash — the comparison is against the current
  hash the drift line already computes, not against the pin.
- Every value a record contributes is escaped on display, and everything
  else `status` prints stays byte for byte what it was.

## Non-Goals

- The gate's `require_agreement` check, the `record-ext` command and any
  reader of an ext record's body, the command that writes
  acknowledgements and the hit surfaces that mark them, `report`'s
  handling of the four types — each has or keeps its own task.
- The declared assignment (implementers, reviewers, independence rules)
  next to what ran — a later task in the same module.
- Showing an ext record's `payload` — it is opaque to the core; the line
  names its hash only.

## Decisions

- **One renderer per type, in the registry.** `RecordRenderer` gains a
  `journal_root` parameter — the renderers that need it resolve the
  journal's own project (`_project_root_for`), which in a sidecar is not
  the invoking checkout's — and the dispatch passes both roots. The
  dispatch still escapes the returned line once, so no renderer can
  forget to and no renderer escapes twice (ADR-0015 decision 5): field
  values go in raw and the whole line is escaped, exactly as the existing
  renderers do.
- **The recorder clause is shared.** `recorded_by=<name>` ends each of
  the four lines; `(not a declared actor)` follows the name when the
  `recorded_by` value is not a key of the journal's project file `actors`
  table — the same membership test `agree` and `reviewer_actor_note`
  make. A `recorded_by_source` of `project-actor` implies declared; an
  override or a git identity can still *name* a declared actor, so the
  test is on the value, not the source. A project file that cannot be
  read declares nothing: the note is shown rather than the line failing —
  the line is a reminder, never an error.
- **Self-acknowledgement is derived, not stored.** `_is_self_acknowledged`
  runs the same `git show -s --format=%an%n%ae%n%cn%n%ce` query
  `_is_self_accepted` runs, returning `None` where git cannot answer —
  rendered as "the mark was not checked" rather than as "not
  self-acknowledged", the same three-way distinction acceptance makes.
  The recorder is a resolved value rather than a typed name, so its side
  of the comparison goes through `_actor_git_identities` — the actors
  table of the journal's own project — plus the recorded name itself
  (an override can be a git identity outright).
- **The agreement line compares against the current hash.** A task with
  no `agreement` record says "no agreement is recorded" — ADR-0018
  decision 2's visibility, so absence is not indistinguishable from
  agreement never asked for. A latest agreement whose `contract` differs
  from `contract_sha256` of `contract.md` as it stands says the agreement
  is for an earlier contract text, naming both short hashes — beside the
  drift line, which compares the pin to the same current hash. When the
  contract cannot be read or hashed the line prints nothing: the
  agreement question then reads as nothing to compare, and `status` still
  answers. Neither line fails the command, projects to state, or is
  required.
- **Only the latest agreement is compared.** An earlier agreement stays
  on its own record line; the summary answers the question a reader asks
  — is what we agreed last still the text in force.

## Migration

None — the change is display-side only. A journal written by a 0.5.0
tool renders the same records; a journal written before schema 7 cannot
carry these four types.

## Risks

- [A hostile or malformed record reaches a renderer through an older
  schema] → the dispatch escapes the whole returned line, and the byte
  pin in `test_status_schema_7_lines.py` demonstrates every field of the
  four types staying on its own line.
- [A renderer could compare the agreement to the pin instead of the
  current hash] → the pin-comparison test covers it: with the contract
  drifted (pin unchanged), the earlier-text line names the current hash.
- [`git show` failing could be read as "not self-acknowledged"] →
  `_is_self_acknowledged` returns `None` there and the line says the mark
  was not checked — the ADR-0007 rule against losing the unanswerable
  case.
- [The recorder clause could disagree with `agree`'s declared-actor
  test] → both test membership in the same `actors` mapping of the same
  project file; `status_view.py` does not grow its own table.
