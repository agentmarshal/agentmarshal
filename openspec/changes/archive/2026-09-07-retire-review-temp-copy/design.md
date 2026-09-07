## Context

See proposal.md — Why. The temp copy predates the pin (CR-054): it existed
because the record kept only finding ids. `write_record` performs its own
refusals (shape, `reviewed_finding` binding, task match, recorder identity,
ULID) and `submit_review` re-implements two of them by hand before writing the
artifact. The gate's collision check runs over `added_records` only. The
operator's `am-land` greps the launcher's stderr for `kept at`.

## Goals / Non-Goals

Goals: one copy of the prose, in the journal; one statement of the pre-write
refusals; artifacts and records under the same collision rule; the baseline
spec true to `report`.

Non-Goals: a capture-policy switch (still a follow-up decision); pinning the
implementer brief; changing the rejected-verdict path, which keeps its temp
copy because no record exists to pin to; cleaning up orphans left by
filesystem failures (they are named, not removed).

## Decisions

- **Retire the temp copy on the accepted path only.** The rejected path has
  no record and keeps its copy. Alternative: keep both copies for
  compatibility — rejected, the copy leaks prose outside the placement that
  decides publication and duplicates evidence.
- **One pre-write refusal in `records`.** A function applies every refusal
  `write_record` applies before its exclusive create — reading the task's
  records for the finding binding and the environment for the recorder's
  identity, as the writer does; `write_record` calls it and so does
  `submit_review` before `write_artifact`. Alternative:
  keep the hand copy in `submit_review` — rejected, two copies of one rule
  drift, and the reviews found exactly that.
- **Residual window is named, not closed.** A filesystem failure or an id
  collision during the record write can still leave the artifact; the command
  reports the artifact's path. Alternative: delete the artifact on failure —
  rejected, deleting under an append-only directory is the wrong reflex, and
  an orphan that is named is recoverable.
- **Collision check over evidence paths.** The same set the append-only rule
  uses (`_is_append_only_evidence_path`) feeds the base-tree collision check.
- **`am-land` follows.** The operator's driver greps `pinned` instead of
  `kept at` on the success path; it is outside the repository and changes
  with this task, not in it.

## Risks / Trade-offs

- [Scripts that parsed `kept at` on success] → the line remains on the
  rejected path; the success path prints `reviewer prose pinned:`. Named as
  BREAKING in the proposal; UPGRADING mentions it at release.
- [Pre-write refusal drifts from `write_record` again] → it is the same
  function, called by both.
- [ADR status notes go stale] → the notes in ADR-0004 and ADR-0005 still say
  reviewer output that names findings is kept in a temporary file; `docs/adr/`
  is outside this task's scope, so they are left to a docs task rather than
  edited here.

## Migration Plan

None for journals: records and artifacts are unchanged. Operators update any
script that parsed the temp-file line.

## Open Questions

None.
