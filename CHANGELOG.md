# Changelog

Notable changes to AgentMarshal. Dates are **PyPI upload dates**, checkable
against <https://pypi.org/project/agentmarshal/#history> — a git tag carries a
local timestamp that can read a day either side of it. The journal under
`.agentmarshal/` carries the per-task evidence behind every entry.

This project describes what it does and not what it intends to do. Where a
capability is partial, the entry says so.

## 0.3.0 — unreleased

The headline is that a journal no longer has to live inside the repository it
records evidence about. Everything else in this release follows from making that
honest: an arrangement that cannot enforce anything must not read as if it does.

### A journal can live in a repository of its own

`agentmarshal init --host PATH` creates a **sidecar** journal: the same journal
structure, the same records, the same commands, in a repository of its own that
names one host repository. The host is read and never written — not its working
tree, not its Git metadata. `init` refuses the two arrangements that would break
that: a journal inside the host's working tree, and a journal that is a linked
worktree of the host, whose commits would land in the host's own object database.

This exists for two situations the embedded placement cannot serve: evidence that
must stay private while the project is public, and a repository you work in but
cannot install anything into.

**The placement is experimental**, and two limits are part of the design rather
than gaps to be closed later:

- **A sidecar gate decides no merge.** It computes every check it can — scope,
  the latest review of the exact commit, reviewer independence, pipeline
  attestation, its own append-only integrity — and says on every run that its
  result is advisory. The merge belongs to the host's process, which a sidecar
  operator does not control. An advisory pass never prints the wording an
  embedded pass prints.
- **A sidecar contract is not pinned to a base commit.** Embedded, the gate reads
  the contract from the base side of the same history as the candidate, so a
  change cannot widen its own scope. A sidecar's contract is not in the host's
  history at all, so it is read from the sidecar working tree, and the gate's
  transcript says so on the scope line. Scope discipline there rests on the
  sidecar's own history.

Every surface that presents evidence carries the placement: `status` and `report`
print it on stderr, leaving their machine-readable stdout unchanged. `validate`,
`prune`, `leak-scan`, `review` and `complete` resolve the host and the journal as
two separate roots. `prune --delete` is refused in a sidecar, because deleting
branches and worktrees would write to the host.

The design and its boundaries are
[ADR-0008](docs/adr/ADR-0008-journal-placements.md); the second
install-and-operate path is [docs/sidecar.md](docs/sidecar.md).

### A session record is accepted after a task closes

`record-session` refused a task that was not open. A task's cost is known when it
ends, so that guard made the one moment worth recording the one moment refused —
and this repository ran forty-eight tasks with no live session record before the
guard was found. The gate has always had a measurements-only lane for exactly
this: a session record changes no state, so accepting one cannot revive or alter
a finished task.

Nothing in the record format changed. What changed is when the tool accepts one.

### The package says where it comes from

`pyproject.toml` declares `[project.urls]`, so the source repository is
discoverable from the package and from the index rather than only from
documentation. It was missing entirely through 0.2.0.

### Compatibility

**No record-format change.** The record schema is 3, as in 0.2.0, and journals
are readable in both directions between the two releases.

One arrangement does not travel backwards: a **sidecar journal requires 0.3.0 on
every checkout that reads it**. A 0.2.0 install does not know the `placement` and
`host` keys. It reads the records correctly — the format is the same — but it
gates the journal repository against itself, classifies the candidate as a
journal-only transaction because everything in that repository is under
`.agentmarshal/`, waives the review requirement that follows from that, and
prints `gate: passed`. Verified against the published 0.2.0. Embedded journals
are unaffected; [UPGRADING.md](UPGRADING.md) has the procedure and the
transcript.

## 0.2.0 — 2026-09-01

The headline is that the operator, not the reviewer, now owns the acceptance
decision — and that a task's lifecycle has a way back. The per-task evidence for
everything below is in the journal.

### Before you upgrade

**A journal written by 0.2.0 cannot be read by 0.1.0.** Records carry fields
and types 0.1.0 does not know, and it refuses records it does not understand —
by design, because a record we cannot validate is not evidence. `validate`,
`status` and the gate all fail closed on the first such record.

The break is one-directional: **0.2.0 reads everything 0.1.0 wrote**, so no
journal needs migrating and nothing is rewritten. Records keep the schema they
were written at.

Everything that runs AgentMarshal against a shared journal must therefore be
upgraded together, before any of them writes a record.
**[UPGRADING.md](UPGRADING.md)** has the procedure and what it means for each
installation method — in particular for an unpinned `pip install`, which moves
on its own schedule and breaks the coordination this requires.

A version mismatch now reports `record has an unknown or missing schema
version` rather than naming an unrecognised field, so the failure says what it
is.

### The operator can accept work over findings

The gate passed an implementation candidate only on an `approved` verdict — the
journal-only lane for openings and completions has never required review — which
meant the acceptance decision belonged to the reviewer while the operator
carried the accountability. (The gate decides; the provider performs the merge.) When review does not converge — remarks changing from round to
round while the verdict stays `changes_required` — the only exits were to
abandon the task or to keep re-running until a verdict happened to approve.

- **`agentmarshal accept`** records that a named party accepted a specific
  commit over specific findings, with a reason.
- It requires the **latest review of that commit to be non-approving**, and
  names exactly the blocking findings that review raised. Review is not
  optional; agreeing with the reviewer is.
- The gate accepts it in place of an approving verdict — **that check and no
  other**. Scope, reviewer independence, pipeline attestation and append-only
  integrity are unchanged.
- An accepted task never reads as an approved one. The gate says
  `accepted over findings … by …; not an approving review`, `status` says it in
  the task summary, and `report` marks the task `decision=accepted-over-findings`.
- Accepting your own work is permitted, and `status` labels it `self-accepted`
  — in the task summary and in the record trail. Where the accepted commit is
  not readable in the current checkout the label cannot be derived, and `status`
  says that rather than falling silent. `report` distinguishes an accepted task
  from an approved one but does not carry the self-acceptance label.

The reasoning, including what an acceptance does *not* establish, is in
[ADR-0007](docs/adr/ADR-0007-operator-acceptance.md).

### The lifecycle has repairs

- **`agentmarshal amend`** records the claim that a task's contract was
  repaired, with the reason. Like every identity and provenance field in this
  project, it is a declaration: nothing detects an unrecorded edit. Previously a defective contract could only be escaped by abandoning
  the task, which left the journal blaming the work for a defect in the
  specification.
- **`agentmarshal reopen`** returns a completed task to `open` with a reason.
  Nothing is rewritten — the completion stays in the trail and the history reads
  as the cycle it was. An abandoned task is not reopenable.

### Contracts reach the implementer

- **`agentmarshal brief`** prints what the journal knows about a task — the
  scope, the acceptance criteria, the rules the tool enforces, and the contract
  body verbatim — to stdout, to be piped into whatever agent does the work. It
  does not know your project's own commands; add those yourself.
  AgentMarshal bundles no implementer and takes no position on which one you use.
- `open` warns when a scope entry names nothing on disk, names a directory
  without its trailing slash, or when a task declares **no scope at all** —
  which forbids every path rather than none.

### Reviews keep their reasoning

- The review prompt names the permitted verdicts, describes `advisory_findings`,
  and asks the reviewer to state each finding's claim in one line of prose.
- The reviewer's raw output is kept when a verdict is refused **or** when a
  recorded verdict names a finding, and the path is reported on stderr. Keeping
  it is **best-effort**: if the file cannot be written the review is still
  recorded, because the record is the evidence and the prose is not. And what is
  kept is what the reviewer wrote — one that emits an id with no prose leaves a
  file with no prose in it.
- A verdict carrying an unsupported field is refused with that field named.

### Records say who wrote them

- Records written by this version carry `recorded_by` and `recorded_by_source`,
  derived from `AGENTMARSHAL_ACTOR` or the invoking checkout's git identity,
  optionally mapped through an `actors` table in `project.json`. Where no
  identity can be determined at all, both fields are **omitted rather than
  guessed**; records written before this release do not carry them.
- This is a **declaration, not authentication** — like `vendor` and `email`. It
  makes the honest case expressible and a false attribution require a second,
  explicit lie. See [ADR-0006](docs/adr/ADR-0006-actors-and-identity.md).
- An agent running the rails should declare itself; the reasoning is in the
  [harness guide](docs/harness-setup.md).

### Economics say where the numbers came from

- A session record may carry `usage.provider` and `usage.method`, where `method`
  is `reported` (the provider stated these counts) or `measured` (they were
  reassembled afterwards, for example from logs).
- `report` carries the distinction through as
  `usage=reported|measured|unrecorded|mixed`, appended after the existing
  fields so a caller splitting on tabs is unaffected.

### Housekeeping

- **`agentmarshal prune`** reports, and with `--delete` removes, the local
  branches and worktrees of tasks the journal says are done. A branch must be
  merged and a worktree must be clean; neither the main worktree nor the one you
  are standing in is ever eligible; deletion never forces, so git's own refusal
  is preserved and reported. No remote is contacted in either mode.
- Renamed from `prune-branches`, which was never released.

### Leak scanning

- **`agentmarshal leak-scan`** scans a candidate diff's **added** content for
  secrets and configured private markers, and the merge path warns on what it
  finds.
- **Advisory and best-effort by design** (ADR-0005): no pattern list can
  enumerate every secret, so a clean scan is never authorization to publish.
  Making it blocking is not in this release.

### Robustness

- `init` reads back the project file it wrote, and `open` reads back the
  contract and the record it wrote; either fails with the path and the
  underlying error instead of reporting success on something nobody can read.
  Reported by an adopter on Windows, where a task directory inherited a
  sandbox's ownership. The outbox README is scaffolded best-effort and is not
  part of that check — a project that could not write it is still initialized,
  and `init` says so.
- `find_git_root` refuses a repository path git reports as non-UTF-8 through the
  project error type instead of raising a decode error out of a function
  contracted to return a path.
- `init` creates `.agentmarshal/upstream/` with a README stating the convention
  for sending findings upstream, and never overwrites one you wrote.

### Documentation

- `CONTRIBUTING.md`, a [quickstart](docs/quickstart.md) and an
  [overview](docs/overview.md) with an explicit implemented-vs-roadmap boundary.
- [`docs/proposals/`](docs/proposals/) — the first adopter batch, digested with
  a stated disposition for every proposal, including the one we declined.
- ADR-0006 (actors and identity) and ADR-0007 (operator acceptance).
- A published [incident record](docs/incidents/) of a warning that grew into a
  path taxonomy over five review rounds, and what it cost.

### Journal format

- Records written by this version carry `schema = 3`. Schemas 1 and 2 keep
  validating.
- New record types: `amendment`, `acceptance`, `reopened`.
- Fields added: `recorded_by`, `recorded_by_source` (any record, when an
  identity is resolvable); `usage` (session records, optional).

## 0.1.0 — 2026-07-30

First public release. The governed loop end to end: contracts with declared
scope, append-only SHA-bound records, state as a projection, and a
provider-agnostic gate that decides fail-closed.

An implementation candidate passes only when scope, an independent review,
pipeline attestation and journal integrity all hold. A journal-only transaction
— an opening or a completion — takes a deterministic lane and needs no review,
since it carries no work to review.
