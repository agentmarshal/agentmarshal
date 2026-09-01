+++
schema = 1
id = "CR-081"
title = "The gate advises in a sidecar, and every surface says which it is"
scope = ["src/agentmarshal/journal/gate.py", "src/agentmarshal/cli.py", "src/agentmarshal/journal/placement.py", "tests/test_gate.py", "tests/test_placement.py", "tests/test_journal.py", "docs/quickstart.md"]
acceptance = [
  "`gate` runs in a sidecar instead of refusing, performing every check it can compute against the host",
  "its transcript states in words that it is advisory and decides no merge, and never prints the authority's wording",
  "`complete` runs in a sidecar and its completed record is written; the transcript says the same thing the gate's does",
  "an embedded journal's gate output is unchanged, byte for byte, including its final line",
  "`status` and `report` state the placement, so evidence read later says which regime produced it",
  "`leak-scan` reads the host in a sidecar, so it stops being the one command with the roots still conflated",
  "no command writes into the host, including its git metadata, and the existing host-inviolability test covers a gate and a complete run",
]
+++

# CR-081: The gate advises in a sidecar

## Context

CR-079 built the sidecar placement and deliberately made `gate` and `complete`
refuse there, because a gate that ran would have had no way to say what its pass
meant. ADR-0008 Decision 5 settled that: in a sidecar the gate **advises** —
every check is still computable against the host, and running it before opening
a pull request in a repository you do not control is exactly its use — but it
decides no merge, because the merge belongs to that repository's own process.

Decision 6 is the constraint that makes it honest: advisory evidence must never
read as gated evidence. This is the principle ADR-0007 already set for
acceptance, applied to placement.

`leak-scan` is the one command CR-079 left with both roots conflated. It binds
to the current checkout, so in a sidecar it scans the journal repository rather
than the host.

## Objective

Let the gate advise, make every surface say which regime produced the evidence,
and finish the root split.

## Acceptance Criteria

- `gate` runs in a sidecar rather than refusing, computing every check it can
  against the host: scope from the base side, the latest review of the exact
  commit, reviewer independence, pipeline attestation, and the journal's own
  append-only and validity checks.
- Its transcript **says it is advisory and decides no merge**, in words, and
  never prints the wording an embedded pass prints.
- `complete` runs in a sidecar and writes its completed record; its transcript
  carries the same statement.
- An **embedded** gate's output is unchanged byte for byte, final line included.
  Adopters read that output, and some parse it.
- `status` and `report` state the journal's placement, so evidence read later
  says which regime produced it rather than leaving the reader to assume.
- `leak-scan` resolves the host in a sidecar.
- No command writes into the host, its git metadata included; the
  host-inviolability test covers a gate run and a complete run.
- The CR-079 test that pins the sidecar **refusal** wording is updated: this
  task removes the refusal it was written to hold.

## Threat model and boundaries

The hazard is **an advisory pass read as an authoritative one** — the same
hazard ADR-0007 named, in a new place. A sidecar gate proves nothing about
whether a change may merge into the host, because the host's process was never
consulted. If its transcript is indistinguishable from an embedded pass, this
task has built a way to produce merge evidence for repositories nobody governs.
That is why the wording is an acceptance criterion and not a nicety.

The second hazard is unchanged from CR-079: **the host learns nothing**
(ADR-0008 Decision 3). A gate reads a great deal from the host — diffs, trees,
commit writers — and every one of those reads must stay read-only, git metadata
included.

Not defects in this task, and not to be guarded against: symlinks, traversal or
TOCTOU on the configured host path, which the operator named in their own
private repository (settled in CR-079); a hostile host, chosen by the sidecar's
owner; the advisory gate being ignored by the host's process, which is the
definition of advisory rather than a flaw.

## Non-Goals

- **Making a sidecar gate authoritative anywhere.** It advises. A host that
  wants enforcement adopts the embedded placement.
- Any policy over which placement a project may use.
- Changing what any check computes. The checks are the same; what changes is
  where the facts come from and what the transcript claims.
- The second install-and-operate document, which follows after we have lived in
  the sidecar ourselves.
