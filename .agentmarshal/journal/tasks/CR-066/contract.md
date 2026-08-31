+++
schema = 1
id = "CR-066"
title = "The gate honours an acceptance, and says it is not an approval"
scope = ["src/agentmarshal/journal/gate.py", "src/agentmarshal/journal/records.py", "tests/test_gate.py", "tests/test_acceptance.py", "docs/quickstart.md", "docs/overview.md"]
acceptance = [
  "the gate passes its review check when the latest review of the candidate is non-approving and a valid acceptance of that exact commit exists",
  "the gate re-derives validity itself: the acceptance must name exactly the blocking findings of the latest review of that commit, and is refused when they differ in either direction",
  "an acceptance for a different commit never satisfies the check",
  "the gate's reported line for an accepted candidate names the accepting party and says it is not an approving review, and never prints the approval wording",
  "every other gate check is unchanged, including reviewer independence, which is still evaluated against the non-approving review",
  "with no acceptance and no approving review the gate refuses exactly as it does today",
  "the quickstart and overview describe the accepted path and state that it is not an approval",
  "an acceptance record carrying a control character in a field the surfaces render inline is refused as invalid",
]
+++

# CR-066: The gate honours an acceptance, and says it is not an approval

## Context

[ADR-0007](../../../docs/adr/ADR-0007-operator-acceptance.md) decided that an
operator may accept a candidate over outstanding findings, and CR-065 built the
record, the command and the surfaces that display it. Nothing yet changes what
merges: the gate still passes only on an approving verdict.

This task is the change that does, and it is the only one in the design able to
weaken the merge authority. It is deliberately alone in its own contract so that
its diff is small enough to read completely.

## Objective

Let a valid acceptance satisfy the gate's review check — that check and no
other — and make the gate's output say plainly which of the two happened.

## Acceptance Criteria

- The review check passes when the latest review of the candidate commit is
  non-approving **and** a valid acceptance of that exact commit exists.
- **The gate re-derives validity from the records itself.** The acceptance must
  name exactly the blocking findings of the latest review of that commit; it is
  refused when they differ in either direction. The gate does not rely on the
  `accept` command having checked this earlier.
- An acceptance naming a different commit never satisfies the check.
- The reported line for an accepted candidate names the accepting party and says
  it is **not an approving review**. The approval wording must not appear.
- Every other check is unchanged — scope from the base side, pipeline
  attestation, append-only integrity, record validity, collisions, lifecycle —
  and **reviewer independence is still evaluated**, against the non-approving
  review, exactly as it is today.
- With neither an approving review nor a valid acceptance the gate refuses with
  its existing wording.
- The quickstart and the overview describe the accepted path, and say it is not
  an approval.

## Threat model and boundaries

The adversary the gate exists for is real and unchanged: a **candidate is
content a contributor supplies**, and everything the gate trusts must come from
somewhere the candidate cannot rewrite. This task must not widen that surface.

Two hazards belong specifically to this change:

- **A stale acceptance.** Findings can grow between an acceptance and a gate
  run: an operator accepts over `F-1`, a later review of the same commit raises
  `F-1` and `F-2`, and the acceptance now covers less than what is outstanding.
  This is why the gate must re-derive the comparison at gate time rather than
  treat the record's existence as proof. Trusting `accept`'s earlier check would
  make a record that was valid once valid forever.
- **An acceptance quietly reading as an approval.** ADR-0007 forbids it, and the
  gate's output is the surface an operator watches most. A merge that happened
  over an objection must be legible as one in the transcript.

  This includes the record's own contents. The accepting party and the finding
  ids are rendered inline by the gate, by `status` and by `report`, so a value
  carrying a newline could add lines to that output — including a line reading
  as an approval. In a single-operator project that is self-deception; in the
  multi-operator setting ADR-0006 describes, it is one party forging what
  another reads. Refusing such a record is the fix, because a value that can
  forge a transcript is not a valid identity.

The following are **not** defects in this task and must not be guarded against:

- symlinks, path traversal or TOCTOU on the journal — the gate reads records the
  way it already does, through machinery this task does not touch;
- the accepting party being unauthenticated. It is a declaration, as the
  reviewer's email already is (ADR-0006); the gate compares declarations and
  says so;
- an operator accepting their own work. ADR-0007 permits it deliberately and
  CR-065 makes it visible; the gate is not the place to re-litigate that.

## Non-Goals

- **Any policy over who may accept.** ADR-0006's configurable override authority
  is a later layer; this task implements no allowlist.
- Changing what `accept` does, or the record's shape.
- Changing any other gate check, its wording, or its order.
- Changing `complete`, which runs the gate and inherits this behaviour without
  needing its own change.
