# ADR-0021: An acknowledged leak-scan hit

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0005](ADR-0005-evidence-capture-and-format.md) (the leak
scan is best-effort — a hit is not proof of a leak and a clean run is
not proof of safety — and the advisory scan at the merge boundary never
blocks), [ADR-0006](ADR-0006-actors-and-identity.md) (actors are
declared, never authenticated; role permissions follow signing),
[ADR-0007](ADR-0007-operator-acceptance.md) (an acceptance substitutes
for the approving-verdict check and nothing else; self-acceptance is
permitted and always marked) and
[ADR-0014](ADR-0014-where-things-live.md) (where the gate reads the
journal's records). **It revises the
[gate-lanes](../../openspec/specs/gate-lanes/spec.md) and
[leak-scan](../../openspec/specs/leak-scan/spec.md) specifications**: a
default gate run on a candidate whose scan reports an acknowledged hit
prints a mark that requirement's pinned transcript does not have, and
the detail the merge boundary shares with the standalone command gains
that mark. It answers the third part of
[proposal 020](../proposals/020-leak-scan-names-no-file-and-self-matches.md).

This ADR records a decision. The record type, the command behaviour and
the gate line it describes are **not implemented by this document**;
they follow in their own tasks. The present tense below is how a
decision is written, not a claim about shipped behaviour.

## Context

How it works today:

- the gate scans the candidate's added lines and warns on a hit —
  `WARN: possible leak in candidate additions (advisory, not
  blocking):` followed by the rendered hits — and decides nothing from
  it: the scan never touches the violations a merge is refused on, and
  on the findings lane it is reported `NOT EXAMINED` for want of a diff
  (`gate.py`);
- `agentmarshal leak-scan --base <ref> --commit <ref>` scans the same
  added lines — the `merge-base..commit` diff — on its own, in any git
  repository, with the configured private markers read from the trusted
  side; it prints each hit as `file: what matched` and exits 1 when it
  found one, 0 when it found none (`cli.py`);
- a hit names the file and the identification of what matched — a
  built-in signature's id, or a private marker's one-based position in
  the configured list — and never the matched text; a path that itself
  carries a marker or matches a signature is printed described, not
  verbatim (`capture.py`: `LeakHit`, `safe_path`, `render_leak_hits`);
- the only suppression the scan has is the declaration's own: a
  private-marker hit whose every occurrence lies in the project file
  that declares the markers is not reported (`capture.py`) — the rule
  the second part of
  [proposal 020](../proposals/020-leak-scan-names-no-file-and-self-matches.md)
  won;
- the scan that refuses a captured artefact before it is stored reports
  the categories it matched and no file: the caller named the artefact
  it offered, so there is no where to add (`capture.py`, the
  [leak-scan](../../openspec/specs/leak-scan/spec.md) specification).

The proposal's third part asks for an acknowledged-and-proceed path
that is recorded rather than bypassed: today an operator who has
checked a hit and found it harmless has nothing to record that with —
the command still exits 1, and the verification evaporates. The
reporter measured what that costs: the transaction had to be completed
outside the tooling, with the reasoning written into the pull request
by hand. The deferral was lifted for the reason the whole intake
moved — the project has taken every adopter finding into the next
release, and this path is among them. That it remains a new kind of
record is why it arrives through a decision record rather than as a
flag — and this is that decision.

## Decision

### 1. A separate record type — an acknowledgement, not a kind of acceptance

An operator who has verified a hit records an **acknowledgement** of
it: a record of its own type in the task's journal, bound to the
candidate the hit was found in.

It is deliberately not a kind of operator acceptance. An acceptance
substitutes for the approving-verdict check and nothing else
([ADR-0007](ADR-0007-operator-acceptance.md)); the gate's leak scan
decides nothing — it warns and never blocks — so there is no check for
an acknowledgement to substitute for. ADR-0007's enumeration of what an
acceptance covers stays closed and unchanged:
[ADR-0013](ADR-0013-extensions-stages-scopes-isolation-trust.md)
extended where an acceptance may stand — over an extension's pause, and
over an operational change — and this decision extends nothing of it.

### 2. What an acknowledgement binds

The record names the candidate's commit, the file, and the
identification of the hit exactly as the scan prints it — a signature
id or a private-marker number, never the matched text — and gives a
reason. It also names who acknowledged, a declared actor as every
record's attribution is.

A hit here is what the added-content scan reports — the only kind of
hit that carries a file: the artefact refusal names categories and no
location, so there is nothing an acknowledgement could name there.

Two properties fall out of binding what the scan prints. The file is
recorded as the scan prints it: a path containing a private marker
already reaches the record masked — `<private marker #N>` — so the
record cannot carry a marker. And an acknowledgement matches a hit only
on the same commit, file and identification — all three — so a new
commit, or a renumbered marker list that changes the identification the
record holds, shows the hit again as unacknowledged: the
acknowledgement fails visible, never silently.

What is recorded is decided here; the field names and the schema
number belong to the later decision on the record model.

### 3. Nothing is hidden — the hit stays printed, marked

The gate, the command and `status` are the surfaces an
acknowledgement prints on. The command still prints every hit, an
acknowledged one marked — acknowledged, by whom, and the reason; the
gate prints the mark on the hits its line shows, within the bound
that line already has — at most twenty, then "and N more not shown",
as the [leak-scan](../../openspec/specs/leak-scan/spec.md)
specification permits; and `status` shows who acknowledged on the
acknowledgement's own line. An acknowledgement never removes a hit
from a surface that shows it, and it neither widens nor narrows the
gate's bound.

What changes is the command's exit status: an acknowledged hit no
longer makes `leak-scan` exit 1. The command still exits 1 on a hit
nobody has acknowledged — an acknowledgement changes what the run
refuses and adds the mark to what it shows; it takes no hit off.

### 4. Any declared actor may acknowledge

There are no roles: binding "who may acknowledge" to a role would be a
permission over unauthenticated identity — the appearance of a control
— which is the reason
[ADR-0006](ADR-0006-actors-and-identity.md) deferred roles until
signing. Roles arrive with signing; this decision introduces none.
The decision pairs admission with visibility: `status` shows who
acknowledged — visibility, not permission, is what the journal can
honestly give.

### 5. Self-acknowledgement is permitted, and marked

A writer of the candidate may acknowledge its own hit. This is
[ADR-0007](ADR-0007-operator-acceptance.md)'s decision 4 applied to the
new record: forbidding it would be satisfied by typing a different
name — identity is declared, not authenticated — and would cost the
feature the configuration that needs it most, a single operator whose
author of record is an agent under the operator's own identity.
Instead the case is made visible: where the acknowledging actor is a
declared writer of the candidate, the mark says the hit was
acknowledged by the commit's author.

The acknowledgement binds the commit it was given on — the
candidate's, not the task's in general: an acknowledgement lives and
dies with the exact commit whose additions it answers.

What the record establishes stays the ADR-0006 boundary, as it does
for an acceptance: someone claiming to be the named actor recorded this
acknowledgement, with this reason, at this time — declared and durable,
not proven.

### The readers and the advisory follow from what is already there

Where an acknowledgement is found follows from where the records it
joins already live: the gate, the command and `status` find
acknowledgements among the journal's records, read where the gate
reads records today — the calling checkout's working tree in the
embedded placement, the journal repository's working tree in a
sidecar ([ADR-0014](ADR-0014-where-things-live.md)). A repository
with no journal has no records to find, and the command behaves there
exactly as today.

And that the scan stays advisory follows from what an acknowledgement
is: a mark on the hits an advisory scan prints, not a verdict the
scan gains. The gate's leak scan stays advisory and never blocks —
with an acknowledgement or without one.

### What this revises

- The [gate-lanes](../../openspec/specs/gate-lanes/spec.md) requirement
  that a default run is unchanged byte for byte: a run on a candidate
  whose scan reports an acknowledged hit prints the mark that
  transcript does not have. A run with no acknowledgement prints
  exactly what it prints today.
- The [leak-scan](../../openspec/specs/leak-scan/spec.md) scenario that
  the merge boundary's line carries the same detail as the standalone
  command: the mark is part of that detail, so the two still agree —
  on the hits its bound lets it show, the boundary's line says what
  the command's does, mark included.

## Left open

- The record model — the acknowledgement record's field names and
  schema number — is a later decision, under
  [ADR-0015](ADR-0015-a-rule-applies-from-the-schema-that-introduced-it.md).
- Whether an acknowledgement would stand over a hit under a blocking
  scan stays open with the scan itself: making a leak-scan hit refuse a
  merge is the roadmap item
  [ADR-0005](ADR-0005-evidence-capture-and-format.md) names, and
  nothing here pre-decides it.

## Consequences

- A verified false positive stays inside the tooling: the operator
  records "reviewed, not a leak" against the commit, file and
  identification, and the command stops refusing the run on its account
  — the recovery
  [proposal 020](../proposals/020-leak-scan-names-no-file-and-self-matches.md)
  measured, outside the tooling with the reasoning left in a pull
  request by hand, becomes a journal record.
- The mark travels with the hit on the three surfaces: an
  acknowledgement changes the command's exit code and adds the mark
  to the hit's line on the surfaces that show it — every hit on the
  command, the hits within the line's bound on the gate — and
  `status` shows who acknowledged on the record's line; it removes a
  hit from none of them.
- `status` gains a line for the record type: today a record type it
  has no line for prints as only its id, its type and its time, so
  showing who acknowledged is part of implementing this decision, not
  something that surface does on its own.
- An acknowledgement cannot silently follow the work: a new commit, or
  a renumbered marker list, shows the hit again as unacknowledged.
- This is a new record type, so a journal containing one cannot be read
  by versions that predate it — the same note
  [ADR-0007](ADR-0007-operator-acceptance.md) carried for acceptance. It
  appears only when the feature is used, so a project that never
  acknowledges a hit never acquires the incompatibility.
- A run with no acknowledgement is byte for byte what it is today: only
  a candidate whose scan reports an acknowledged hit changes the
  transcript.

## Alternatives considered

**A kind of operator acceptance.** Refused — an acceptance substitutes
for a check the gate would otherwise fail, and the leak scan fails
nothing: the record would pretend to override what never refused. It
would also stretch
[ADR-0007](ADR-0007-operator-acceptance.md)'s closed enumeration over a
check that is not in it.

**An ignore list or a suppression flag.** Refused — the proposal asked
for the path to be recorded, not bypassed: a suppression hides the hit
from every later reader, while the acknowledgement keeps the hit
printed and adds the mark. Hiding is precisely the failure the record
exists to prevent.

**Bind the acknowledgement within the task, not to the commit.**
Refused — a new commit carries additions the acknowledgement never
saw; under a task-wide binding the hit would stay marked while what it
matched changed, the invisible failure this design refuses. Binding to
the commit is what makes a stale acknowledgement fail visible.

**Require an acknowledger other than the candidate's writers.**
Refused — ADR-0007's decision-4 reasoning stands: a different-name rule
is satisfied by typing a different name under declared identity, and it
would remove the feature from the single-operator configuration that
needs it. The case is marked instead.

**Record the matched text for audit.** Refused — the record cannot
carry the secret: a private marker is itself the sensitive string,
which is why the scan names it by position. The record binds the hit by
the same identification the scan prints, and no more.
