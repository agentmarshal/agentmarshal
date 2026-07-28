+++
schema = 1
id = "CR-026"
title = "ADR-0005 evidence capture policy and attestation format"
scope = ["docs/adr/ADR-0005-evidence-capture-and-format.md"]
acceptance = []
+++

# CR-026: ADR-0005 evidence capture policy and attestation format

## Context

A journal revision (2026-07-28) found that measurements (token economics)
were never written to the durable journal — the `session` record type
exists but only gitignored v1-format `runs/stats` data holds economics —
and that full review text / prompts / sessions live only in gitignored
`runs/`. ADR-0004 D7 anticipated a per-class capture policy that was never
built. The founding brief (§12) plans in-toto / SLSA compatibility as a
"standard envelope, not predicate". This ADR decides the capture policy,
how measurements relate to the task lifecycle, the sanctioned retroactive
backfill of historical host data, and the format strategy that keeps the
journal forward-compatible with in-toto / SLSA without ever converting it.

## Objective

Record the architectural decision (ADR-0005) covering: capture policy,
measurements independent of lifecycle, retroactive backfill, and the
records-as-source-of-truth / in-toto-as-derived-projection format
strategy with the invariant that even the minimal preset stays
in-toto / SLSA complete.

## Acceptance Criteria

- [ ] `docs/adr/ADR-0005-evidence-capture-and-format.md` exists, Accepted,
      and decides at least: (1) a capture policy — preset
      (minimal/attested/full) plus per-type overrides, with a mandatory
      leak-scan; (2) attestation records are always-on and carry the full
      in-toto/SLSA-required field set, while the capture policy governs
      only supplementary artifacts (review text, prompts, raw sessions)
      and economics — with the invariant that no capture setting drops
      the journal below in-toto/SLSA completeness, enforced by
      `validate`; (3) measurements accrue independent of lifecycle
      (`session`/measurement records may be appended after a terminal
      record; lifecycle records stay immutable after terminal); (4)
      retroactive backfill of retained host raw data into the journal,
      provenance-marked (live vs imported-from-host) and leak-scanned;
      (5) the format strategy — flat records are the source of truth,
      in-toto Statement / DSSE / Sigstore are a derived projection
      (wave-2), with a compatibility matrix, the fields to add
      (contract hash, artifact reference + hash, provenance), and a
      predicateType URI registry.
- [ ] The ADR states the honest caveats: retroactive backfill needs
      retained raw data; imported evidence is provenance-weaker than
      live-captured; `minimal` is in-toto/SLSA complete but omits
      AgentMarshal's economics enrichment.
- [ ] It references ADR-0004 (extends D7) and the brief (§12/§13).
- [ ] `uv run agentmarshal validate` and the CI checks stay green.

## Non-Goals

- No implementation in this slice — decision record only. The
  capture-policy config, the gate/status change for measurements
  post-terminal, the backfill tool, the record-schema fields, and the
  in-toto projection are later CRs. No code or schema change here.

