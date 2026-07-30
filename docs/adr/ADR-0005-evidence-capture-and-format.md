# ADR-0005: Evidence capture policy, measurements, and attestation format

Status: Accepted
Date: 2026-07-28

> **0.1.0 implementation boundary.** This ADR records the *decided design*
> and is largely a roadmap. Implemented in 0.1.0: the always-on lifecycle
> records (`opened`, `review`, `completed`, `abandoned`) and the
> `session`/measurement record type — validated fail-closed and read by the
> gate. **Planned, not implemented in 0.1.0** (no active enforcement):
> supplementary-artifact capture and the capture-policy presets/overrides
> (Decision 2) — `capture.py` is a stub that writes nothing; the mandatory
> pre-commit leak-scan (Decision 2); the in-toto Statement / DSSE projection
> and the schema fields it needs (Decisions 1 and 5) — `attestation.py` emits
> no Statement; and the retroactive host backfill (Decision 4). Sentences
> below that describe these in the present tense state the target behaviour,
> not what 0.1.0 does. The Decision 5 "activation boundary" notes mark where
> each guarantee becomes enforced.

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
   ever converting the journal, so the derived attestation can feed an
   external compliance pack for auditors (brief §13).

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

**Invariant.** in-toto **Statement** completeness — a syntactically
derivable in-toto Statement carrying AgentMarshal's own predicate — is a
property of the always-on attestation records, not of the capture policy.
No capture setting drops the journal below in-toto Statement
completeness. **This is normative intent, not a property the current
validator enforces.** Its **activation boundary** is the schema-fields +
validate-check slice (Decision 5): only once those fields land and the
check ships will `agentmarshal validate` reject, fail-closed, a
review/completed record that is not in-toto-Statement-derivable-complete.
Until then this ADR does not represent the guarantee as enforced; after
activation a user cannot accidentally turn interoperability off.

This guarantee is the **in-toto Statement layer** (`subject`,
`predicateType`, `predicate`) carrying AgentMarshal's own predicate. The
**DSSE Envelope layer (signing) is a distinct in-toto layer and lies
outside this activation boundary** — it is introduced by the wave-2
signing slice (Decision 5), not by the completeness invariant. It is
**not** a SLSA conformance claim: SLSA Source (v1.2) additionally requires trusted
identities, enforced protected-reference controls, approval bound to the
final revision, and contemporaneous source attestations — process- and
provider-level properties our record fields cannot establish. SLSA
Source alignment is adjacency and roadmap (Decision 5), never asserted as
a derived level.

### 2. Capture policy — preset plus overrides *(planned; not implemented in 0.1.0 — see the boundary above)*

Host configuration selects a **preset** and may **override** per class:

| preset | economics | reviews / prompts | raw sessions |
|---|---|---|---|
| `minimal` | off | off | off |
| `attested` (default) | commit | hash (private store) | hash (private store) |
| `full` | commit | commit | **private store** (never public by preset) |

- Per-type overrides layer on the preset (e.g. `reviews = commit` under
  `attested`); only when a real mixed need appears — no speculative
  matrix (ADR-0004 D6).
- **Raw session transcripts stay private by default at every preset**,
  preserving ADR-0004 D7's private-only rule. `full` raises observability
  by capturing full review/prompt text and economics, and by keeping
  sessions in a durable **private store** (hash-referenced from public
  records) — not by publishing them.
- **Public session commit is a separate, explicit escalation that
  supersedes ADR-0004 D7 only for that narrow case**, and requires **two
  independent opt-ins**: persistent configuration (`allow_public_sessions`)
  **and** a per-operation dangerously-named flag. Neither alone suffices.
- **Leak-scan is mandatory** on every artifact before it is committed
  *(planned; no leak-scan runs in 0.1.0)*: secrets, private hosts and tokens
  are refused. Leak-scan is an
  additional safeguard, **not authorization to publish** — it never
  substitutes for the opt-ins above; heuristics miss content, so private
  stays the default.
- `minimal` is in-toto Statement complete but omits AgentMarshal's
  economics enrichment; this is documented, not silent.

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

### 5. Format — records are source of truth, in-toto is a projection *(projection planned; not implemented in 0.1.0 — see the boundary above)*

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

| in-toto Statement field | record field | status |
|---|---|---|
| `subject[].digest` (`gitCommit`) | `reviewed_commit` / `completed_commit` | present |
| `predicateType` (URI) | derived from `record_type` via a URI registry | add registry |
| `predicate` (body) | verdict / reviewer / findings / tokens | present |
| contract the review bound to | contract content hash | **add / derive from committed contract** |
| supplementary artifact | artifact reference + hash | **add** |
| evidence provenance | `source` + import metadata | **add** |
| reviewer identity (an *input* to SLSA Source two-party review, not proof of it) | `reviewer.email` + git writers | present |
| schema version | `schema` | present, evolvable |

Fields derivable from always-committed data (commit digests, the
committed contract's hash, git author/committer emails) need not be
stored; they are computed at projection time, so they cannot be turned
off.

The projection guarantee is scoped to the **in-toto Statement layer
carrying AgentMarshal's own AI-review `predicateType`** — a syntactically
valid, **schema-checkable** in-toto Statement. The DSSE **Envelope** layer
is a separate in-toto layer, out of scope until the wave-2 signing slice. Structural validity is all
the unsigned projection asserts: its producer and integrity become
cryptographically **verifiable only once the DSSE/Sigstore signing of
wave 2 wraps it**, so "verifiable attestation" is reserved for that signed
output; the unsigned Statement is schema-valid, not a verifiable
attestation. AgentMarshal is **SLSA Source-Track
adjacent, not SLSA-conformant**: the reviewer-identity field is an input
a SLSA Source verifier *could* consume, but a Source level (e.g. two-party
review at L4) additionally demands trusted-identity configuration,
enforced protected-reference controls, final-revision binding, and
contemporaneous source attestations that live at the provider/process
layer. Reaching a stated SLSA Source level is a roadmap item requiring
that separate specification (a fixed SLSA version, the trust config, and a
VSA), and is deliberately **not** claimed as derivable from the records
alone. Once the schema fields land, the derived (and later signed)
Statement is what feeds an external auditor via the compliance pack
(brief §13); that is the scope of this format guarantee.

## Consequences

- Once the projection ships (Decision 5), the minimal footprint a user can
  select will still project to a complete, interoperable in-toto Statement;
  economics and full artifacts are additive. In 0.1.0 no Statement is
  emitted. SLSA Source conformance is a separate roadmap goal, not part of
  this floor.
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
