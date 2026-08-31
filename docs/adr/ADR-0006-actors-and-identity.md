# ADR-0006: Actors, declared identity, and multi-operator work

Status: Accepted
Date: 2026-08-31

## Context

Two questions arrived together and turned out to be one question.

**Can two human operators share a project?** The evidence model says yes:
records are append-only with collision-resistant identifiers (ADR-0004), state
is a projection, the contract is read from the base side so no one widens their
own scope, and separate checkouts remove the working-tree contention that a
single shared tree would create. Nothing in the journal contends.

**But the identity layer does not exist.** Records do not say who created them.
The gate's independence check compares the recorded reviewer's email against the
commit authors' — a string comparison between two declarations.

This project then demonstrated the consequence on itself. Six review records
marked `vendor: human` under an operator's address were produced by an agent.
Every gate passed, including the line `PASS: reviewer is independent of the
candidate's writers`. Nothing in the evidence distinguishes those records from
ones a person created.

With one operator that is self-deception. With two it becomes impersonation of a
colleague, and the record looks identical either way. Adopter proposal 003 (roles
bound to scope) was deferred on the grounds that enforcement over unauthenticated
identity manufactures the appearance of a control; that reasoning now has a
demonstration behind it and belongs in a decision rather than a disposition note.

ADR-0001 speaks of "trusted recorders". This ADR states what that trust does and
does not buy.

## Decision

### 1. An actor is the party a record is attributed to, and it is declared

An **actor** is whoever a record is attributed to: a human operator, an agent, a
model reviewer, a CI job. Actors are **declared, never authenticated** — until
signing exists, the journal cannot establish that a declared actor corresponds
to anyone.

Records gain **`recorded_by`**: the actor that created the record, kept separate
from the record's semantic fields (a review's `reviewer`, a session's `actor`).

`recorded_by` is **derived, not typed**. Actors are declared in an `actors`
section of `.agentmarshal/project.json`, each with an identifier and the git
identities that map to it. The tool resolves `recorded_by` by matching the
invoking checkout's `user.email` against that table; with no match, or no
`actors` section, it records the git identity itself, so a project that
configures nothing still gets a value. A caller may override it, and the record
then also carries the fact that it was overridden — an override that hides
itself would defeat the field. Precise field names and schema version belong to
the implementing task; what this ADR fixes is that the value comes from the
environment by default and that an override is visible.

A field the caller simply types would add nothing over the labels we already
have.

**What this buys, stated exactly.** It does not prevent a false attribution. It
separates two claims that are conflated today: *who is said to have reviewed* and
*who created the record*. When those differ — an agent recording a human's
verdict — the record now says so, instead of being silent. The honest case
becomes expressible, and the dishonest one requires a second, explicit lie.

### 2. What the journal claims before signing

This narrows what the journal claims **about identity**. It leaves every other
gate guarantee untouched — scope compliance, pipeline attestation, append-only
integrity, record validity, collision detection and lifecycle consistency are
unaffected by this ADR and continue to mean what they say.

About identity specifically, and until review records are signed, AgentMarshal
claims exactly this and no more:

- a review record exists, is well-formed, append-only, and bound to a commit SHA;
- the **declared** reviewer identity differs from the **declared** authors and
  committers of the range.

It does **not** claim that those identities correspond to real parties, that any
party read anything, or that the recorder is who it says. `vendor`, `model`,
`email` and `recorded_by` are all labels chosen by whoever ran the command.

**The tool's own output must say this.** The gate's independence line reads as if
a review were validated; it validates a string. Its wording must name what is
compared — a declared identity — so the output cannot be mistaken for evidence of
human involvement. The same correction applies anywhere the documentation implies
otherwise.

This is the deliberate boundary, not an oversight: an unenforceable claim printed
as a `PASS` is worse than no claim, because it is believed.

### 3. Decision rights are project policy, opt in, defaults unchanged

Who may review, who may overrule findings, and whether one actor may carry a task
from opening to completion are **project decisions**, not properties of the tool.
They become configurable policy, evaluated at the same declared level as
everything above:

- **distinct-actor review** — the reviewer must be a different declared actor
  than the implementer, not merely a different email string;
- **override authority** — which actors, if any, may accept work over outstanding
  findings, and never the actor who implemented it;
  *(the default in the table below is superseded by
  [ADR-0007](ADR-0007-operator-acceptance.md), which builds the mechanism
  proposal 007 asked for: an acceptance exists, and one by a writer of the
  candidate is permitted and always visible. This clause survives as the policy
  a project may adopt once that layer is built.)*
- **end-to-end by one actor** — permitted by default; a project may forbid it.

Each default is stated, because "defaults unchanged" is otherwise ambiguous:

| Policy | Default | What holds today |
|---|---|---|
| distinct-actor review | **off** | the existing declared-email comparison remains the only check |
| override authority | **no override exists** *(superseded by [ADR-0007](ADR-0007-operator-acceptance.md))* | the gate merges only on `approved`; nothing changes until proposal 007 is built |
| end-to-end by one actor | **permitted** | unchanged |

Existing adopters run one operator and must not be broken by an ADR. A policy
that is not configured is not enforced, and the gate reports which policies were
in force.

### 4. Multi-operator coordination adds no new machinery

Two operators need three things that already work or need only discipline:

- **A checkout each.** This is the natural arrangement and it removes the single
  worst hazard — two parties sharing one working tree, where the uncommitted
  review record of one is clobbered by the other's branch switch.
- **Task numbers.** Allocation is `max + 1` scanned in the invoking checkout, so
  two simultaneous `open` calls take the same number. The remedy is process:
  **land the opening first** — it is journal-only, takes the deterministic lane,
  and merges in seconds, after which the number is visible to everyone. A
  reservation mechanism is **deliberately not added**: the collision is caught
  fail-closed at merge, the process remedy costs nothing, and a lock is machinery
  that would have to be maintained for a problem measured in minutes of rework.
- **Disjoint scope.** Two open tasks may declare overlapping scope and nothing
  objects: the gate checks a candidate against **its own** contract and has no
  view of other open tasks. What eventually stops the collision is git refusing
  an unmergeable content conflict — a different mechanism, later, and only when
  the same lines are touched. Operators should therefore agree scopes up front.
  An advisory cross-task warning is worth adding later; a refusal is not, because
  overlapping scope is sometimes correct.

### 5. What this ADR does not decide

- **Signing.** The real remedy for declared identity is a signed review record
  (ADR-0005, wave 2). This ADR fixes the first thing worth signing: not the build
  artifact, but the human approval, because that is the strongest claim the
  system makes and the cheapest to forge.
- **Role permissions** (proposal 003). Binding scope to a role requires an actor
  that can be authenticated; it therefore follows signing, not this ADR.
- **Lifecycle hooks** (proposal 009). Policy evaluated by the gate is not a hook:
  it runs no third-party code and widens no trust surface. Hooks remain a
  separate question.

**Dependent corrections.** Accepting this ADR leaves user-facing documentation
contradicting it, and those are named here so the contradiction is tracked rather
than tacit: `docs/quickstart.md` ("independence is the property AgentMarshal
makes durable, so it is enforced") and `docs/overview.md` ("Enforced, not
assumed") both describe the email comparison as enforcement of independence.
They must be reworded to declared-identity comparison, together with the gate's
own output line, as the first task following this ADR.

## Consequences

- Two operators can work honestly today under process discipline — a checkout
  each, openings landed first, disjoint scope, and **the other operator reviews**.
  That last point is the real gain: with two operators the independence check
  finally compares two different parties instead of one party wearing two
  addresses.
- The journal becomes able to record that an agent created a record on a human's
  behalf. It still cannot detect a determined false attribution, and the
  documentation says so rather than implying otherwise.
- Every identity check in the system is explicitly a declaration check until
  signing lands. Anything built on identity before then — roles, override
  authority — inherits that limit and must state it.
- Defaults do not change, so existing single-operator adopters are unaffected by
  this ADR until they opt into a policy.
