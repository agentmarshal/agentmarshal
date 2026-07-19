# ADR-0004: Journal data model — documents for contracts, append-only records for evidence

Status: Accepted
Date: 2026-07-19

## Context

The journal is the center of the product
([ADR-0001](ADR-0001-governance-plane.md)): a durable evidence ledger
living in the repository. That imposes hard requirements: evidence must
be portable (plain git-tracked files — no external database, leaving
must be lossless), reviewable, conflict-free under parallel tasks
([ADR-0002](ADR-0002-unit-of-isolation.md)), machine-validated
fail-closed, selectively loadable (one task's records must be
self-sufficient), and extractable for later evaluation of executors.

Operating the v1 rails supplied the failure catalogue. A single mutable
document per task with a parsed text header worked, but: a gate that
parsed prose verdicts broke on a wording change; a mutable status field
inside the contract made gate behavior depend on which branch was
checked out; and any shared mutable file is a merge conflict between
parallel branches waiting to happen.

One industry data point frames the storage question: the most visible
git-native task tracker for agents abandoned git-as-database for an SQL
database in 2026 under multi-writer and query load. The transferable
lesson is narrower than "git does not work": what breaks git-as-storage
is shared mutable state edited across branches, at query scales far
beyond a single repository's task history. Our writers are bounded (task
openings are serialized per ADR-0002, recorders write within a task's
branch), and evidence portability is a product requirement — so the fix
is a model that avoids cross-branch mutation, not a database.

## Decision

1. **Two kinds of journal data.**
   - **Contracts are documents**: human-authored markdown with a
     machine-readable TOML header (task id, scope paths, acceptance
     criteria) parsed by the standard library. Contracts change only
     through explicit journal transactions; git history is the
     amendment trail.
   - **Evidence is append-only records**: reviews and verdicts,
     completion evidence, lifecycle events, execution inputs (the
     prompt snapshot a session was actually launched with,
     content-addressed and captured by the launcher at launch time),
     and measurements. One file per record, JSON, written exactly once
     by a trusted recorder, never edited. Record identity is
     unconditionally unique: every record path embeds the task id and a
     recorder-generated sortable unique identifier (ULID-class), plus
     the reviewed commit where applicable; records are created with
     exclusive-create semantics, and an already-existing path is an
     error, never an overwrite. Parallel branches therefore cannot
     collide on a path.

2. **State is a projection.** A task's status is computed
   deterministically from its records — opened, review recorded,
   merged, completed — never stored as a mutable field. No materialized
   state files are committed.

3. **Machine layer and human layer are separate.** The JSON record is
   the source of truth for machines; prose renderings may accompany it
   for humans. Gates never parse prose.

4. **Validation is fail-closed and stdlib-only.** Contract headers and
   records are validated on load against versioned schemas by explicit
   validators; an unparseable record, an unknown schema version, or an
   internally inconsistent one (a blocking verdict with zero findings)
   is an error, not a warning. No third-party validation dependency in
   the core; this is revisited only if schema complexity outgrows
   hand-written validators.

5. **Layout is task-scoped.** Everything about a task lives under its
   own directory; reading one task never requires scanning the journal.

6. **Storage sits behind a seam.** All journal I/O goes through the
   recorder (write) and loader (read/projection) APIs; gates, CLI and
   reports never touch journal files directly. v2 ships exactly one
   storage implementation — git-tracked files. If multi-writer or query
   pressure ever materializes, the sanctioned escalation is a derived
   database index over the same records; the repository remains the
   source of truth for evidence permanently, since portable evidence is
   the product. This is a seam, not an adapter framework: no
   speculative interface ceremony beyond a single I/O boundary.

7. **Records carry a visibility class.** Public records live in the
   repository. Private records live in a persistent local store outside
   git (optionally synced to a private remote); a public record may
   reference private content by hash, attesting to it without
   disclosing it. Per-class capture policy is explicit host
   configuration: prompt snapshots public, private or off; generated
   artifacts hash-only; full session transcripts only into the private
   store and only under a double opt-in (configuration plus an
   explicitly dangerous-named flag) — never into the public store.

## Consequences

- Journal transactions from parallel tasks merge without conflicts by
  construction; the only serialized journal write remains task creation
  (ADR-0002).
- Gates read state from records reachable from the merge candidate
  instead of the checked-out working tree, removing a whole class of
  checkout-order traps observed on the v1 rails.
- No file ever says "status: done"; humans ask the CLI. The CLI being
  the product's API, this is accepted.
- Machine-readable acceptance criteria plus recorded outcomes make
  every merged task an extractable evaluation case with no extra
  bookkeeping.
- Session records may carry an optional external trace reference,
  keeping the ledger composable with session observability tooling
  without depending on it.
- Records declare their schema version from day one; loaders reject
  versions they do not know.
- This repository's own v1-format journal becomes the first test case
  for the migration tooling the model implies.
