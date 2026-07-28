# ADR-0005: Evidence capture policy, measurements, and attestation format

Status: Accepted
Date: 2026-07-28

## Context

Operating the v2 journal surfaced three gaps against
[ADR-0004](ADR-0004-journal-data-model.md) and the founding brief:

1. **Measurements were never durable.** ADR-0004 D1 lists measurements
   among evidence records and the `session` record type exists, but no
   session record was ever written. Token economics lives only in
   gitignored `runs/stats` host state (v1 format), lost on re-clone.
2. **The per-class capture policy of ADR-0004 D7 was never built.** Full
   review text, prompt snapshots and raw session transcripts sit only in
   gitignored `runs/`; the committed review record carries a verdict and
   finding ids but not the finding text, so the durable attestation is
   opaque without the host artifacts.
3. **in-toto / SLSA compatibility (brief §12, wave 2) has no design.**
   The records are custom JSON. The requirement is to be forward
   compatible with the in-toto Attestation Framework and SLSA without
   ever converting the journal.

This ADR decides the capture policy, how measurements relate to the task
lifecycle, the sanctioned retroactive backfill of retained host data, and
the format strategy. It extends ADR-0004 D7.

## Decision

### 1. Two layers: always-on attestation, policy-governed supplements

- **Attestation records are always on.** The lifecycle records
  (`opened`, `review`, `completed`, `abandoned`) and their in-toto /
  SLSA-required fields are written unconditionally — the gate requires
  them and they are the source of truth. The capture policy cannot
  disable or reduce them.
- **The capture policy governs only the supplementary layer**:
  supplementary artifacts (full review text, prompt snapshots, raw
  session transcripts) and economics (`session`/measurement records).

**Invariant.** in-toto / SLSA completeness is a property of the always-on
attestation records, not of the capture policy. No capture setting drops
the journal below in-toto / SLSA completeness. `agentmarshal validate`
enforces it fail-closed: a review/completed record that is not
in-toto/SLSA-derivable-complete is rejected. A user cannot accidentally
turn interoperability off.

### 2. Capture policy — preset plus overrides

Host configuration selects a **preset** and may **override** per class:

| preset | economics | reviews / prompts | raw sessions |
|---|---|---|---|
| `minimal` | off | off | off |
| `attested` (default) | commit | hash (private store) | hash / private |
| `full` | commit | commit | commit only with `allow_public_sessions` |

- Per-type overrides layer on the preset (e.g. `reviews = commit` under
  `attested`); only when a real mixed need appears — no speculative
  matrix (ADR-0004 D6).
- Committing raw session transcripts publicly requires the explicit
  `allow_public_sessions` double opt-in (ADR-0004 D7).
- **Leak-scan is mandatory** on every artifact before it is committed:
  secrets, private hosts and tokens are refused. `full` without leak-scan
  would be a disclosure vector.
- `minimal` is in-toto / SLSA complete but omits AgentMarshal's economics
  enrichment; this is documented, not silent.

### 3. Measurements accrue independent of lifecycle

A completed task's **lifecycle is immutable** — no further `opened`,
`review`, `completed` or `abandoned` record may be added. But
**measurements are not lifecycle**: `session`/measurement records (and
supplementary artifacts) may be appended to a task in any state,
including terminal, because they project to no lifecycle state.

- Status projection admits a `session` record after a terminal record;
  it still rejects a lifecycle record after a terminal one.
- The gate admits a candidate that adds only `session` records (and
  non-record artifacts) to a task closed at base; it still refuses
  lifecycle records on a closed task. Append-only and collision checks
  are unchanged.
- This enables both recording economics at or after completion and the
  retroactive backfill below, through the normal validating gate rather
  than an override.

### 4. Retroactive backfill of retained host data

Raising the capture level may be applied retroactively: retained host raw
data (`runs/`) is imported into the journal under the current policy.

- **Provenance is marked.** Imported records carry
  `source = imported-from-host` with the import time and the hash of the
  source raw file; live-captured records are `source = live`. Imported
  evidence is provenance-weaker than live-captured (it is not attested at
  the moment of the event); verifiers must distinguish them. AgentMarshal
  does not present backfill as live attestation.
- **Only possible while raw data is retained.** After a low capture
  policy plus cleanup, there is nothing to import.
- **Leak-scanned** on import exactly as forward capture.

### 5. Format — records are source of truth, in-toto is a projection

The journal is **not** stored in in-toto format. Flat records remain the
source of truth (gate and validators read fields directly, ADR-0004 D3).
The in-toto Statement, its DSSE envelope and Sigstore signing are a
**derived projection** generated on demand for the compliance pack — never
the storage format. The journal is therefore never converted; a new or
evolved target format is re-derived (ADR-0004 D6: derived outputs over the
same records, repository stays source of truth).

To keep the derivation **lossless** (a projection, not a conversion) the
record schema must carry every field the target formats need. The
compatibility matrix:

| in-toto Statement / SLSA | record field | status |
|---|---|---|
| `subject[].digest` (`gitCommit`) | `reviewed_commit` / `completed_commit` | present |
| `predicateType` (URI) | derived from `record_type` via a URI registry | add registry |
| `predicate` (body) | verdict / reviewer / findings / tokens | present |
| contract the review bound to | contract content hash | **add / derive from committed contract** |
| supplementary artifact | artifact reference + hash | **add** |
| evidence provenance | `source` + import metadata | **add** |
| independence (SLSA Source L4 two-party) | `reviewer.email` + git writers | derivable |
| schema version | `schema` | present, evolvable |

Fields derivable from always-committed data (commit digests, the
committed contract's hash, git author/committer emails) need not be
stored; they are computed at projection time, so they cannot be turned
off. We are SLSA **Source-Track adjacent**, not SLSA provenance: same
in-toto envelope, our own first AI-review `predicateType`.

## Consequences

- The minimal footprint a user can select is still a complete,
  interoperable attestation; economics and full artifacts are additive.
- Economics and observability become durable and auditable; token-overspend
  and review-loop cases can be reconstructed from committed data.
- Sigstore signing (DSSE) is deferred (wave 2) but requires no journal
  change — it wraps the derived Statement.
- Retroactive backfill is honest: imported evidence is labelled and is
  weaker than live capture; this ADR does not blur the two.
- New schema fields (contract hash, artifact reference, provenance) and
  the predicateType registry are added before the backfill so history and
  forward capture are written in-toto-complete from the start.
- Implementation follows in later slices: the capture-policy config with
  leak-scan, the status/gate change for measurements post-terminal, the
  schema fields and predicateType registry, the backfill tool, and the
  in-toto projection.
