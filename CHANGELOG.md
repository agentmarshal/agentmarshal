# Changelog

Notable changes to AgentMarshal. Dates are **PyPI upload dates**, checkable
against <https://pypi.org/project/agentmarshal/#history> — a git tag carries a
local timestamp that can read a day either side of it. The journal under
`.agentmarshal/` carries the per-task evidence behind every entry.

This project describes what it does and not what it intends to do. Where a
capability is partial, the entry says so.

## 0.4.1 — 2026-09-24

A patch release for one defect an adopter hit on 0.4.0, plus the documentation
and release machinery that landed with it.

### `validate` reads a journal 0.4.0 refused (CR-114)

0.4.0 refused a finding id, an acceptance field, a finding summary, an artifact
reference or a contract header entry containing any character Python's
`str.isprintable()` calls unprintable. That test is false for every space
separator but a plain space, so a journal an earlier release had written could be
refused for a narrow no-break space inside a finding id — and the records of a
closed task cannot be repaired. The rule now names what it refuses: Unicode
categories `Cc`, `Cs`, `Zl`, `Zp` and the bidirectional marks, embeddings,
overrides and isolates. One predicate decides it for records, contract headers
and the artifact reference `validate` checks, so the three cannot drift.
**If 0.4.0's `validate` refused a record your earlier release accepted, this
release reads it again** — see [UPGRADING.md](UPGRADING.md). Records written on
0.4.0 are unaffected: where the rule refused a write, nothing was written.

### The default branch says it is not a release (CR-112)

Between releases the version carries a `.dev0` suffix, so a build from the
default branch no longer reports the same version as the published release;
CONTRIBUTING states the rule, and the release workflow refuses to publish a
development or local version.

### Token counts are not what a provider charges (CR-113)

Proposal 024 is published with its disposition: a session the provider refused
to continue is recorded with the outcome `provider-limit`, a documented value
that the tool neither checks nor counts, and the quickstart and README no longer
present token counts as what a task cost. The reset time a provider states in
its refusal still has no field; that waits for the accounting rework proposal
018 deferred.

## 0.4.0 — 2026-09-18

The headline is that work which is not a source diff can now be recorded and
reviewed as evidence, while the ordinary diff lane has gained more explicit
inputs and checks. The release also closes several paths where the tool's
writer, gate, or diagnostics disagreed with the evidence model.

Three record schemas are new (CR-086, CR-096, CR-106), and 0.3.0 cannot read a
journal containing any of them: schema 4 for a finding and the records bound to
one, schema 5 for a review carrying the hash of its contract — every review
`agentmarshal review` records — and schema 6 for a coordination session. Read
[UPGRADING.md](UPGRADING.md) before any of them is written to a shared journal.

### Findings land as evidence, not a diff (CR-085, CR-086, CR-101)

ADR-0009 defines the findings lane. An empty-scope research task can record a
hash-pinned `finding`, review and accept it by finding rather than commit, and
gate and complete it with `--findings`; a task with declared scope remains in
the diff lane. `agentmarshal review --reviewed-finding` launches the configured
reviewer on locally verifiable artifacts and refuses the launch if their bytes
drift from the recorded hashes. Artifacts that cannot resolve locally are
reported as not verified; a finding with none that can be verified is refused.

### Process tools have a declared footprint (CR-087, CR-088, CR-089, CR-090)

Contract-header schema 2 adds declared `decisions`, `documents`, and
`extensions`. Briefs and reviewer prompts carry that named material; the gate
reads the base-side manifest to add an extension's footprint to effective scope,
require named documents to be touched, and check a removed manifest's former
footprint. It executes no manifest command. OpenSpec 1.12.0 is the first
declared extension in this repository, with its git-visible footprint and the
machine-local files it does not commit recorded in its manifest.

### Review evidence names both prose and contract (CR-091, CR-092, CR-095, CR-096, CR-111)

The capture policy's `reviews` class decides what happens to a review's prose.
By default (`hash`) it stays out of the journal: the private store that level
names is not built, so `agentmarshal review` keeps the reviewer's standard
output in a local temporary file and names it. With
`capture.overrides.reviews = "commit"` the output is written and pinned as a
journal artifact, and `submit-review --prose FILE` attaches human prose the
same way; at any other level `--prose` is refused. Only the `reviews` class is
read; the `economics` and `sessions` classes are not. Pinned artifacts are validated
under the same collision and append-only rules as records, and a foreseeable
refusal leaves no orphan artifact. Briefs and review prompts show that a
contract was amended, when, and why, and reviews record the hash of the contract
text they judged.

### The gate reads one candidate listing and can state its limits (CR-093, CR-099, CR-103, CR-105)

Every path-sensitive gate check reads one listing in which a rename has both
its deletion and addition. `--without-review` evaluates the checks independent
of review and marks the two review-bound checks as not examined when no review
exists; it never relaxes a review record that does exist. A reopening of a
completed task now passes the gate's additive-record rule. The gate's leak-scan line
shows at most twenty hits and counts the rest; the standalone command prints
every hit. The shipped GitHub workflow uses the
review-free mode rather than tolerating a check that cannot carry its own review.
That is partial coverage: on GitHub, nothing shipped enforces the
approved-independent-review requirement, because the required check runs
before the review exists (see `docs/github-enforcement.md`).

### Reviewer setup reports its actual preconditions (CR-097, CR-098)

The reviewer-command contract, rejected placeholder, and a no-recording
`review --dry-run` exercise are documented. `agentmarshal init` prints the
preconditions the tool cannot verify — provider merge settings, the agent's
declared actor, the reviewer command, a CI step that runs `validate` — with what
skipping each costs. `agentmarshal doctor` checks the last three and reports an
unmet one as a `TODO` line, never printing the reviewer command's value; an unmet
precondition does not change its exit status, and its summary line counts the
preconditions left instead of claiming that every check passed.

### Writers preserve journal readability (CR-102)

Commands that add records to an existing task now ask the lifecycle projection
whether it admits the record. A write that would make the projection refuse the
task is rejected instead of leaving an invalid append-only journal; sessions
and a permitted reopening retain their projection-defined exceptions.

### Coordination is a recorded session activity (CR-106)

`record-session` accepts `coordination` beside implementation, review, and
other. Only a coordination session uses record schema 6; the other activities
retain their prior schema.

### Adopter findings made diagnostics actionable (CR-094, CR-100)

Ten sanitized adopter findings and their dispositions are published with a way
to follow each accepted item. A leak-scan hit now identifies the file and a
built-in signature or configured marker position without printing the secret;
the scan does not report a marker where it occurs in the configuration that
declares it, and reports every occurrence anywhere else. A reviewer command's
diagnostics on a successful run are kept outside the journal with their path
named, and the generated upstream outbox says it is not evidence.

### Documentation and reporting are easier to enter (CR-084, CR-107, CR-108)

The documentation was reconciled with the released tool and its workflow. New
contributors can find the security-reporting channel, structured finding and
gate-refusal forms, the pull-request requirements, and a documentation map.

### Internal consolidation (CR-104)

The review launcher paths share their tail and identity resolution has one
home; this changes no command behaviour.

## 0.3.0 — 2026-09-01

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

The surfaces that present evidence say which regime produced it: `status` and
`report` print the placement on stderr, leaving their machine-readable stdout
unchanged, and the gate and `complete` transcripts say it in words.

`open`, `gate`, `complete`, `review`, `prune` and `leak-scan` resolve the host
and the journal as two separate roots. `validate` is the exception, and not an
oversight: it checks the journal it is run in, and a sidecar's host has no
journal to check. `prune --delete` is refused in a sidecar, because deleting
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

It is metadata and nothing more: it changes no behaviour, it does not establish
that a given build came from that repository, and it cannot be backfilled into
0.2.0 — the metadata of a published release is immutable.

### Compatibility

**No record-format change.** The record schema is 3, as in 0.2.0, so every
**record** either release writes is read by the other. That is a statement about
records, not about the tool as a whole — the paragraph below is the part it does
not cover.

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
