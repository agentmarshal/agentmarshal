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
     prompt snapshot a session was launched with, content-addressed at
     launch time — *planned; not captured in 0.1.0, see D7 and
     ADR-0005*), and measurements. One file per record, JSON, written
     exactly once
     by a trusted recorder, never edited. Record identity is
     collision-resistant by construction: every record path embeds the
     task id and a recorder-generated sortable collision-resistant
     identifier (ULID-class), plus the reviewed commit where
     applicable. Records are created with exclusive-create semantics —
     an already-existing path is an error, never an overwrite — and the
     merge gate performs fail-closed collision detection at
     integration: a merge candidate introducing a record path that
     already exists on the target branch does not merge. Collisions are
     therefore detected at the boundary, not assumed away.

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

   **0.1.0 boundary.** This is the target visibility model. In 0.1.0
   every record is public and git-tracked; the persistent private
   store, the per-class capture policy, prompt-snapshot capture, and the
   session double-opt-in are **planned, not implemented** (`capture.py`
   writes nothing). ADR-0005 marks the same capture boundary.

   **Status in 0.2.0.** The historical boundary still applies to durable
   supplementary capture: the parser exists, but there is no policy-driven
   artifact writer or private store. An advisory added-content leak-scan now
   ships at the gate and as `agentmarshal leak-scan`; reviewer output that
   names findings is also preserved best-effort in a temporary file. Neither
   is the capture/private-store design decided here.

## Consequences

- Journal transactions from parallel tasks never contend over shared
  mutable files; identifier collisions are statistically negligible and
  caught fail-closed at the merge boundary if they ever occur. The only
  serialized journal write remains task creation (ADR-0002).
- Gates read journal records from the checkout they are invoked on — the
  **trusted-checkout** model documented in the README and self-hosting
  docs. The merge-authority wrapper checks out the merge candidate and
  runs the gate there, so the gate sees the candidate's records rather
  than whatever tree a human happened to leave behind; the gate trusts
  that checkout and does not independently resolve records from the
  candidate SHA. This removes the checkout-order traps of the v1 rails
  while keeping the trust boundary explicit (an untrusted caller can run
  the gate on a mismatched tree — the wrapper, not the gate, guarantees
  the checkout matches the candidate).
- No file ever says "status: done"; humans ask the CLI. The CLI being
  the product's API, this is accepted.
- Machine-readable acceptance criteria plus recorded outcomes *would*
  make a merged task an extractable evaluation case with no extra
  bookkeeping — but only once contracts actually carry them. In practice
  the machine-readable `acceptance` array was empty in every contract
  through CR-038 (criteria lived only as human prose in the body); the
  v1→v2 migration carried no contract prose at all. So most merged tasks
  are **not** usable evaluation cases today (see
  [docs/migration-v1-to-v2.md](../migration-v1-to-v2.md)). Substantive,
  machine-readable acceptance is required going forward, and enforcing it
  in the gate is a planned contract-schema change, not yet in effect.
- Session records may carry an optional external trace reference,
  keeping the ledger composable with session observability tooling
  without depending on it.
- Records declare their schema version from day one; loaders reject
  versions they do not know. Schema 3 denotes records written with the
  schema-2 provenance rules plus creator attribution (`recorded_by` and
  `recorded_by_source`). The bump makes a reader/writer version mismatch
  legible as an unsupported schema instead of misreporting those fields as
  invalid. Loaders continue to accept schemas 1 and 2 unchanged, so existing
  journals require no migration.
- This repository's own v1-format journal becomes the first test case
  for the migration tooling the model implies.
