+++
schema = 1
id = "CR-039"
title = "opening honesty: align ADR-0004/0005 with 0.1.0 + v1-to-v2 migration-loss note"
scope = ["docs/adr/ADR-0004-journal-data-model.md", "docs/adr/ADR-0005-evidence-capture-and-format.md", "docs/migration-v1-to-v2.md"]
acceptance = [
  "ADR-0004: capture / private-store / session-opt-in claims are marked planned (not active in 0.1.0), not present-tense",
  "ADR-0004: the gate 'candidate-reachable state' claim is replaced with the actual trusted-checkout model (gate reads the invoking checkout)",
  "ADR-0004: the 'every merged task is an extractable evaluation case' claim is corrected to acknowledge thin early/migrated contracts",
  "ADR-0005: capture presets, mandatory leak-scan, in-toto projection, and 'complete Statement' are marked roadmap with an explicit 'implemented in 0.1.0' boundary",
  "docs/migration-v1-to-v2.md honestly records the v1->v2 contract-prose loss and thin early contracts, without backfilling any historical contract",
  "no code behavior change; validate, pytest, ruff, format, mypy stay green",
]
+++

# CR-039: opening honesty: align ADR-0004/0005 with 0.1.0 + v1-to-v2 migration-loss note

## Context

An open-readiness audit (maintainer + an independent Codex reviewer) found
that ADR-0004 and ADR-0005 describe unimplemented behaviour in the present
tense — forward artifact capture, a persistent private store, session opt-in,
mandatory pre-commit leak scanning, and an on-demand in-toto projection —
while `capture.py` writes nothing and `attestation.py` emits no Statement.
ADR-0004 also claims the gate reads "candidate-reachable" records (it reads
the invoking checkout) and that every merged task is an extractable evaluation
case (early and v1->v2-migrated tasks have thin, sometimes empty contracts).
Before the repository is made public, the shipped design docs must state what
0.1.0 actually implements, and the contract-prose loss during the v1->v2
migration must be documented honestly rather than papered over.

## Objective

Make the shipped ADRs honest about the 0.1.0 boundary and record the
v1->v2 migration loss as a durable, non-fabricated note — so that opening the
repository exposes an accurate account, not overstated guarantees.

## Acceptance Criteria

- [ ] ADR-0004: capture, private-store, and session-opt-in behaviour is marked
      planned / not-active-in-0.1.0 (no present-tense "captured", "stored",
      "double opt-in" as if live).
- [ ] ADR-0004: the "candidate-reachable" gate claim is replaced with the
      trusted-checkout model already documented in README/self-hosting docs.
- [ ] ADR-0004: the "every merged task is an extractable evaluation case"
      claim is corrected to acknowledge that early/migrated tasks have thin
      contracts (pointer to the migration note).
- [ ] ADR-0005: capture presets, mandatory leak-scan-before-commit, the
      in-toto projection, and the "complete interoperable Statement" claim are
      marked roadmap, each under an explicit "implemented in 0.1.0" boundary.
- [ ] `docs/migration-v1-to-v2.md` records: the v1->v2 migration did not carry
      contract prose; early v2 / bootstrap contracts (e.g. CR-001..018, and
      the release tasks) are thin; substantive contracts are REQUIRED going
      forward (RFC planned) — framed as "being introduced", not "done". It
      does NOT backfill or rewrite any historical contract.
- [ ] No code behaviour change; `uv run agentmarshal validate`, pytest, ruff,
      format, and mypy stay green.

## Non-Goals

- No backfilling or rewriting of historical contracts or records (that would
  fabricate evidence — the CR-033 R1 lesson) and no git history rewriting.
- No code change: ADR prose plus one new doc only.
- No contract-schema change and no gate enforcement of acceptance criteria —
  that is the separate contract-extension RFC.
- Not a full public narrative / promotion doc — only the honest boundary +
  migration note needed for opening.
