# ADR-0008: Journal placements and what each placement can claim

Status: Accepted
Date: 2026-09-01

This ADR records a decision. The mechanism it describes is **not implemented by
this document** — the configuration, the command changes and the documentation
split follow in their own tasks. The present tense below is how a decision is
written, not a claim about shipped behaviour.

## Context

The journal lives in `.agentmarshal/` inside the governed repository, and the
rails depend on exactly that: the gate reads a task's contract from the base
side of the same history the candidate belongs to, so a change cannot widen its
own scope, and the evidence travels in the same clone as the code it attests.
Where the operator controls the repository, this is the strongest available
arrangement and it does not change here.

But it makes one assumption that is false for two classes of user we can point
at rather than imagine.

**An operator whose working evidence is private.** A project can be public
while the material its method runs on is not: research notes, pre-registered
findings, incident context, coordination that names people or clients. That
material is invisible to the tool — no records, no SHA binding, nothing in
`report` — even though the method's own practices depend on it. Keeping it as
loose files beside the repository means the part of the evidence that most
needs timestamps and immutability has neither.

**A practitioner who does not control the repository.** An engineer working in
an employer's repository cannot install anything into it — not a directory, not
a config file, not an ignore rule. Practitioners in this position demonstrably
build the journal anyway, by hand: numbered PRD files in a personal directory,
attempt logs, artifacts per task, multi-model review rituals driven by prompt
(a public example: the RA PID workflow write-up, telegra.ph, 2026-08). The
demand for the journal exists without the rails; today the tool offers nothing
between "adopt everything in your repo" and "nothing".

The operator set three requirements for the design: private and public journals
must coexist over one project **without duplication and without the private
side's existence leaking into the public repository**; the tool must be usable
**without rails**; and the answer must own its documentation consequences.

## Decision

### 1. Placement is a property of a journal, and the tool stays one tool

A journal has a **placement**:

- **embedded** — `.agentmarshal/` inside the governed repository. Today's
  arrangement, unchanged, and the default.
- **sidecar** — the same journal structure in a repository of its own, which
  names one **host repository** and records evidence about it.

There is no separate product, no "lite" build, and no divergent format: the
same commands, the same record schema, the same validation. A sidecar journal
differs in where it sits and in what its evidence can claim — nothing else.

### 2. A task lives in exactly one journal

State is a projection of a task's records, and a projection with two sources is
ambiguous by construction. No task's records are split across journals, and no
state is ever projected across journals. An operator running both an embedded
and a sidecar journal over one project runs two journals with disjoint tasks —
public lifecycle in one, private work in the other — not one journal in two
places.

### 3. References flow from private toward public, never back

A sidecar journal references its host freely: the host's identity, its commit
SHAs, and — where the host carries an embedded journal — its task ids. All such
reading is read-only.

**The host repository carries no reference to, and no marker of the existence
of, any sidecar.** Not a link, not a config key, not a placeholder record, not
an ignore rule. A reader with full access to the host repository and its
embedded journal must be unable to tell whether a sidecar exists at all. This
is the operator's requirement stated as an invariant, and it is deliberately
absolute: an ignore rule alone would disclose exactly what it is hiding.

One consequence is accepted openly: hash-pinned references from public records
to private artifacts (`artifacts: [{ref, hash}]`, ADR-0005) disclose that
private evidence **exists**, even though not what it says. They remain
available — pinning a pre-registration by hash is a legitimate, deliberate act
of disclosure — but they are an explicit opt-in and never a default, and no
machinery writes one on the operator's behalf.

### 4. A sidecar lives outside the host's working tree

Not inside it under an ignore rule, and not as a submodule. An ignored
directory inside the host tree is one careless `git add -A` away from becoming
public history, and the ignore rule itself is a marker that something exists —
both fail Decision 3 in one stroke. Submodules were considered and rejected in
both directions: host-as-submodule makes the repository colleagues and CI use
non-canonical, and journal-as-submodule requires writing to the host, which is
the wall this placement exists to respect.

A sidecar is an ordinary repository somewhere the operator controls, holding
`.agentmarshal/` and a configuration that names the host. Teams share one the
way they share any repository.

### 5. Without rails, the gate advises and everything else works

In a sidecar journal the full journal machinery works as it does today: `open`,
`brief`, `status`, `report`, `amend`, `reopen`, `abandon`, `submit-review`,
`review`, `accept`, `record-session`, `validate`. They read the host where they
need git facts — resolving a commit, snapshotting a tree for review, naming a
commit's writers — and write records in the sidecar.

The **gate runs advisory**. Every check it performs is still computable — scope
against the host diff, the latest review of the exact commit, reviewer
independence, append-only integrity of the sidecar — and running it before
opening a pull request in the host is exactly its use. What the gate does not
do in this placement is **decide a merge**, because the merge belongs to the
host's own process, which this operator does not control. The transcript says
so in words, on every run; an advisory pass never prints as the authority's
pass.

ADR-0009 Decision 4 defines the findings-lane exception to this rule.

### 6. Advisory evidence is always distinguishable from gated evidence

The principle is the one ADR-0007 set: a thing that happened without an
authority must never read as if the authority approved it.

A journal's placement is declared in its configuration, and every surface that
presents evidence — the gate transcript, `status`, `report`, and the
attestation projection when it exists — carries the placement with it. A
completion recorded in a sidecar states that its checks passed **advisorily**;
nothing in it claims a merge authority was satisfied, because none was
consulted.

ADR-0009 Decision 4 defines the findings-lane exception to this rule.

### 7. What sidecar evidence establishes, and what it does not

In the manner of ADR-0006, stated rather than implied.

Sidecar evidence establishes the same declarations embedded evidence does —
who is said to have reviewed what commit, with what verdict, recorded by whom,
at what time — bound to the host's SHAs and append-only **within the sidecar's
own history**. They remain declarations in ADR-0006's sense: identities are
declared, not authenticated, and nothing establishes that the named party read
anything. Placement changes none of that in either direction.

It does not establish that any of it was enforced. The append-only property of
a sidecar is protected only by the sidecar's own governance — its owner can run
the same journal-only checks this project runs on itself, and nothing stops an
owner who does not. And no property of the host repository is attested beyond
what its SHAs pin: the host merged whatever its own process merged.

That is materially weaker than the embedded, gated arrangement, and materially
stronger than the hand-rolled alternative it replaces — files with dates typed
into them, in a directory with no history discipline. The documentation states
both halves of that sentence with equal weight.

## Consequences

**The documentation forks, and that is most of the cost.** Installation,
initialization and the operating loop currently assume the embedded placement
throughout. A second install-and-operate path — a journal without rails — cuts
across roughly half the user documentation and is budgeted as its own work, not
as a footnote to the code.

**Our own operation gets a home for its private evidence.** A sidecar over this
repository can hold research-class records — including pre-registered findings,
which earn journal timestamps instead of dates typed into files. The deferred
adopter proposal 005 (a record type for research findings) has a natural place
to land when it is re-read.

**The adoption on-ramp inverts.** Today the first step is the largest —
install into the repo. With a sidecar the first step is private and reversible:
keep the journal, gain the evidence, bring the rails to a repository you
control when you choose. The hand-rolled-PRD practitioner is the persona this
serves.

**A new failure mode to watch.** The private side referencing the public side
means private contracts and records will quote host paths and task titles.
Nothing about that leaks — the flow is inward — but an operator later
*upstreaming* material from a sidecar (a proposal, an incident write-up) is
performing declassification by hand, and the documentation for that workflow
must say so.

## Alternatives considered

**A separate "lite" product.** Rejected: a fork of the format and the
maintenance, and the name itself concedes divergence. Placement is a property,
not a product.

**Submodules, either direction.** Rejected above (Decision 4): one direction
makes the working repository non-canonical, the other requires the write access
whose absence defines the problem.

**Splitting one task's records across journals.** Rejected (Decision 2):
state is a projection, and two sources make it a guess.

**Public-side links to private evidence as the bridge.** Rejected as a default
(Decision 3): a link discloses existence, which is precisely what the
requirement forbids; kept as explicit opt-in where disclosure is the point.

**Doing nothing — the private side stays loose files.** Rejected by the
evidence: the practice this project most depends on for catching its own
defects ran on files whose timestamps prove nothing, and the practitioners this
would serve are already building journals by hand.
