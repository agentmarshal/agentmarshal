# Overview — what AgentMarshal is and how it works

A short brief on the product's purpose, the core idea, a simplified picture
of how it is built, the vocabulary it uses, and where it is heading. For a
hands-on setup, see the [Quickstart](quickstart.md).

## Purpose

Agents produce more changes than a human can read. AgentMarshal makes **"this
work was independently reviewed"** a durable property of the *repository*
rather than of someone's memory or a vanished chat log. It does two things:

- **Attestation** — records what was done, by whom, reviewed by whom, bound to
  the exact commit, as evidence that lives in git.
- **Merge governance** — a gate that lets a change merge only when that
  evidence holds (in scope, independently reviewed, pipeline-attested).

It is **vendor-neutral** (works on GitHub, GitFlic, or a self-hosted setup) and
**model-agnostic** (bundles no reviewer; you wire in whichever model or human
does the reviewing).

## The core idea

Everything is **evidence in git**. There is no server and no database — a
project's whole governance history is committed files under `.agentmarshal/`.

Two properties make that trustworthy:

- **Records are append-only and SHA-bound.** A review names the exact commit it
  assessed, and an operator acceptance names the exact commit and blocking
  findings accepted over. You cannot retroactively edit either; you can only
  append.
- **State is a projection, never a stored field.** A task's status (`open`,
  `done`, `abandoned`) is *computed* from its records. Nothing ever writes
  `status: done` by hand, so the status cannot lie about the evidence.

## How it works (simplified)

```
   contract (scope + acceptance)          append-only records
   .agentmarshal/journal/tasks/CR-001/    (opened / review / completed)
                    │                              │
                    └──────────────┬───────────────┘
                                   ▼
                          agentmarshal gate
              reads git + the journal; passes only when
              every check holds (scope, independent review,
              pipeline attestation, append-only integrity)
                                   │
                    pass ──────────┴────────── fail (fail-closed)
                     │
                     ▼
        your provider performs the merge
        (GitHub / GitFlic / self-hosted wrapper)
```

- You **open** a task with a declared **scope**. Its contract is committed
  first, so it is in the base before any work builds on it. `brief` delivers
  that contract to an implementer; `amend` records a later contract repair.
- You **implement** within scope on a branch, and an **independent** reviewer
  records a verdict for the exact commit.
- If that latest verdict is non-approving, an operator may record acceptance of
  that exact commit over exactly its blocking findings. The gate re-checks that
  correspondence when it runs. Acceptance substitutes only for an approving
  verdict; it is **not an approving review**.
- The **gate** — the merge authority — reads git and the journal and decides.
  It is provider-agnostic: it never performs the merge itself; the provider
  does, gated on the gate's answer.
- **Completion** re-runs the gate and writes the durable `completed` record.
- **Reopening** appends a reason and projects a completed task back to `open`;
  it does not erase the earlier completion. `prune` reports removable local
  branches and worktrees after work is done.

The gate reads the contract and prior task state from the **base** side, never
from the candidate, so a change can never widen its own scope or hide that its
task is already closed.

## Terminology

- **Host repo** — the repository that *adopts* AgentMarshal to govern its own
  work (your project). Distinct from the AgentMarshal tool/package itself. You
  run `agentmarshal init` in the host repo; the journal lives there.
- **Placement** — where a journal sits relative to the repository it records
  evidence about: **embedded** (inside it, the default, everything below
  assumes it) or **sidecar** (a repository of its own naming a host, which it
  only ever reads). Sidecar is new in 0.3.0 and **experimental**; its gate
  advises and decides no merge. See [sidecar.md](sidecar.md) and
  [ADR-0008](adr/ADR-0008-journal-placements.md).
- **Journal** — everything under `.agentmarshal/journal/`: the per-task
  contracts and records. The single source of truth, committed to git.
- **Task** — a unit of governed work (id like `CR-001`), living in
  `.agentmarshal/journal/tasks/<id>/`.
- **Contract** — a task's specification: a TOML header (id, title, **scope**,
  **acceptance** criteria) plus a markdown body. Committed before the work.
- **Scope** — the paths a task is allowed to change. The gate refuses a diff
  that touches anything outside it.
- **Record** — one append-only JSON evidence file: `opened`, `review`,
  `acceptance`, `amendment`, `completed`, `reopened`, `abandoned`, or a
  `session` (measurement). Written once, never edited.
- **Projection / state** — a task's status computed from its records, never
  stored.
- **Review** — a recorded verdict (`approved`, `changes_required`, …) for an
  exact commit, carrying the reviewer's identity.
- **Acceptance** — an operator's recorded decision to ship an exact commit over
  all blocking findings in its latest non-approving review. It is not an
  approval and does not bypass reviewer independence or any other gate check.
- **Reviewer independence** — the gate requires the recorded reviewer's email to
  differ from the commit's authors/committers, and refuses the merge otherwise.
  It is a comparison of *declared* identities: nothing establishes that the
  declared reviewer is a real party, or that anyone read the change. Signed
  review records are roadmap (ADR-0006).
- **Candidate / base / merge-base** — the commit being gated, the target it
  merges into, and their common ancestor. The gate diffs `merge-base..candidate`
  and reads trusted inputs from the base side.
- **Pipeline attestation** — the invoker's assertion that a green pipeline ran
  for the exact candidate commit (see `AGENTMARSHAL_PIPELINE_OK_SHA` and the
  `--attestation` modes in the [Quickstart](quickstart.md)).
- **Gate** — `agentmarshal gate`: the provider-agnostic merge authority. Passes
  fail-closed only when every check holds.
- **Lane** — the gate recognizes two kinds of change: a **journal-only** (a.k.a.
  deterministic) transaction — one that touches nothing outside `.agentmarshal/`,
  such as an opening, a completion, a contract amendment or a reopening — needs
  no review; an **implementation** candidate takes the full review-bound lane.
- **Merge authority** — the gate *decides*; the provider *merges*. A host
  wrapper (e.g. `am-merge` / a GitHub Action) runs the gate and, on a pass,
  performs the merge.

## Direction (roadmap)

The design is broader than the shipped 0.3.0 repository version; the honest
boundary is stated in the ADRs and
[migration-v1-to-v2.md](migration-v1-to-v2.md). What is designed but **not
active in 0.3.0**, in rough order (features land in later releases —
`agentmarshal --version` shows yours):

- **Verifiable attestation** — projecting records to an in-toto Statement and
  signing it (DSSE / Sigstore), so provenance is cryptographically checkable,
  not just recorded. Adjacent to (not a claim of) SLSA Source; not yet emitted.
- **Capture policy** — token-economics/session records accrue in 0.3.0
  (`record-session` / `report`). What is roadmap is the *capture policy* that
  governs retaining heavier supplementary evidence — full review and prompt
  text, raw session transcripts — public or in a private store. In 0.3.0 the
  policy parser exists but no policy-driven writer or private store retains
  those artifacts. Reviewer output with findings is kept separately in a
  best-effort temporary file; that is not policy-governed durable capture.
- **Mandatory leak-scan enforcement** — 0.3.0 ships a standalone `leak-scan`
  command and an advisory merge-time scan that warns on possible leaks in a
  candidate's additions. Making a match block is roadmap. The scan is
  best-effort by design (ADR-0005) — never a guarantee.
- **Contract-extension RFC** — required machine-readable acceptance criteria
  plus a threat-model field, so every merged task doubles as an evaluation
  case and gates enforce it.
- **Broader providers** — first-class GitHub, GitFlic, and self-hosted rails.

See the [ADRs](adr/) for the full design decisions.
