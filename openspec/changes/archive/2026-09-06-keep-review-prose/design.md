## Context

See proposal.md — Why. Constraints: records are files under
`tasks/<id>/records/` with ULID names and are append-only; `artifacts` is an
existing schema-2 record field (`[{ref, hash}]`) written today by the
backfill importer and by `finding` records (ADR-0009); the gate's append-only
check keys on record paths; the review launcher validates the verdict
before writing the record and keeps rejected output under the temp
directory. Capture policy (ADR-0005) distinguishes evidence that is always
kept from supplements a policy governs.

## Goals / Non-Goals

Goals: the prose lands in the journal with the record that cites it, pinned
by hash, under the same immutability as records; the two review paths do it
the same way; nothing changes for a journal that keeps no prose.

Non-Goals: a structured findings format (SARIF or otherwise) — the prose is
kept verbatim; redaction; a capture-policy switch for prose (this release
keeps it whenever a verdict is accepted; a policy knob is a later decision);
pinning the implementer brief.

## Decisions

- **Location: `tasks/<id>/artifacts/<record-id>-review.md`.** Beside the
  record, named by the record's id, so the two are found together and the
  name cannot collide. Alternative: inside the record as a field — rejected,
  records stay small and the prose is not part of the verdict; a shared
  `artifacts/` root — rejected, evidence belongs with its task.
- **Pin, do not embed.** `artifacts: [{ref, hash}]` on the review record, the
  existing schema-2 shape (ADR-0009): the record says which bytes it cites.
- **Write the artifact before the record**, so a record never cites a file
  that does not exist; the record write is the existing exclusive write.
- **Append-only extends to `artifacts/`.** The gate's rule for record paths
  applies to artifact paths under a task; `validate` verifies pinned hashes.
  Alternative: trust the record — rejected, a pinned hash nobody checks is a
  field filled in by eye.
- **Verbatim, unredacted.** The prose is what the reviewer wrote; the leak
  scan already runs over candidate additions in the completion transaction.

## Risks / Trade-offs

- [Prose contains code excerpts a private project would not publish] →
  the journal's placement decides publication (ADR-0008); a policy switch is
  a follow-up, named in Non-Goals.
- [Large outputs] → one file per review; no cap in this change; size is
  observable in `status`.
- [Two writers of `artifacts` now (finding, review)] → one helper writes
  an artifact and returns its pin; both call it.

## Migration Plan

None: old records carry no `artifacts` and behave as before; nothing is
backfilled.

## Open Questions

None that change the specs or the approach.
