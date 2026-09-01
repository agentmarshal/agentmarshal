# Migration v1 → v2: what did not carry over

This note records, honestly and without backfilling, what was **lost or
left thin** when AgentMarshal moved from the v1 rails to the v2 journal.
It exists so that a reader of the public history is not misled by the
design ADRs into thinking the journal has always been as rich as the
target model describes. Nothing here rewrites or fabricates a historical
contract — the gaps are stated, not papered over.

## 1. v1 contract prose was not migrated

The v1 tooling tracked work differently. When v2 introduced the
contract-per-task model (a TOML `+++` header plus a markdown body — see
[ADR-0004](adr/ADR-0004-journal-data-model.md)), the earlier v1 task
descriptions were **not** carried into v2 contracts. There is no v2
contract reconstructing the intent of pre-v2 work. This prose is simply
gone from the journal; the git history remains the only record of that
period.

We deliberately do **not** reconstruct it after the fact. Writing a
plausible-looking contract for a task that never had one would fabricate
evidence — the same failure the CR-033 R1 lesson forbids — and would be
indistinguishable, to a later verifier, from a contemporaneous record.
An honest gap is worth more than a convincing invention.

## 2. The machine-readable `acceptance` array was empty until CR-039

Every v2 contract has a markdown `## Acceptance Criteria` section written
for humans. But the **machine-readable** `acceptance` array in the TOML
header was left empty (`acceptance = []`) in every contract from CR-001
through CR-038. **CR-039 is the first contract to populate it.**

Concretely, as of this note: 38 of 39 task contracts carry
`acceptance = []`. The consequence, stated plainly in
[ADR-0004](adr/ADR-0004-journal-data-model.md)'s consequences, is that
the "every merged task is an extractable evaluation case" property does
**not** hold retroactively. Most merged tasks cannot be turned into
machine-checkable evaluation cases, because the criteria a machine would
check were never recorded in machine-readable form — only as prose a
human must read.

## 3. Early bootstrap contracts are thin

Beyond the empty acceptance arrays, the earliest v2 bootstrap contracts
(roughly CR-001..018) and the release-plumbing tasks are thin: short
context, no threat model, no non-goals, minimal structure. They were
enough to move the bootstrap forward but are not the substantive
contracts the design assumes. They are kept as-is; they are not
retro-fitted.

## 4. `scope_allow` did not carry over, and nothing replaced it by that name

v1 had a `scope_allow` mechanism for constraining what a task might touch. It
did not survive into v2 and was never mentioned here — an omission an adopter
found the hard way while looking for it (proposal 003).

In v2 the contract's **`scope`** is the only scope mechanism: declared when the
task is opened, committed to the base before work builds on it, enforced by the
gate against the candidate's diff. There is no per-actor or per-role scope —
that is a deliberate boundary (see ADR-0006 and proposal 003's disposition),
not a lost feature: enforcement bound to a declared, unauthenticated identity
would only look like a control.

## 5. Empty v1 directories: `integrations/`, `plugins/`

v1 scaffolding created `.agentmarshal/integrations/{ci,git,provider}` and
`.agentmarshal/plugins/`. The published v2 `init` creates none of them —
verified against an installed 0.1.0 and current source — and nothing in v2
reads them. If your project carries them over from v1, they are empty slots
with no consumer: delete them.

## What changes going forward (being introduced, not done)

- **Substantive, machine-readable acceptance is required for new
  contracts.** CR-039 is the first to carry a non-empty `acceptance`
  array and full Context / Objective / Acceptance / Non-Goals prose; it
  is the pattern for what follows.
- **Gate enforcement is planned, not yet in effect.** Making the gate
  reject a new task whose contract has empty acceptance (while
  grandfathering the existing thin ones via a schema-version bump) is a
  contract-schema change tracked by a separate RFC. Until that ships,
  the requirement above is convention, not enforcement.
- **No history is rewritten.** The thin and empty contracts stay in the
  journal exactly as recorded. Their SHA-bound trail is the product's
  audit value; erasing the gaps would erase the evidence of how the
  project actually evolved.

This note itself is the honest boundary: it says what is missing and why
we are not inventing it back.
