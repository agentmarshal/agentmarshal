# ADR-0010: Process tools plug in through a declared footprint, not a hook

Status: Accepted
Date: 2026-09-06

This ADR records a decision. The manifest, the contract fields and the gate
check it describes are **not implemented by this document**; they follow in
their own tasks. The present tense below is how a decision is written, not a
claim about shipped behaviour.

## Context

AgentMarshal governs a change: contract, independent review, gate, cost,
journal. It does not produce the system's documentation, task graphs, specs or
any other process artifact — and it should not (ADR-0001: a governance plane;
harness-specific glue confined to thin adapters. ADR-0004: "a seam, not an
adapter framework").

Two signals say the seam is missing:

- An adopter declined AgentMarshal in favour of OpenSpec: a living, agent-written
  system description fed into the model's context, updated with every change.
  Their own onboarding guide names the weakness of that discipline — specs "go
  stale, because nothing forces them to track reality". Forcing things to track
  reality is what a gate does.
- Proposal 009 asked for lifecycle hooks so that a project-defined step (store
  an artifact before `complete`) is enforced rather than remembered. It was
  deferred: a hook that runs during the gate blurs what the gate trusts, and a
  hook interface is easy to add and hard to remove.

Bundling any such tool is rejected: the adopter chose one tool because it was
one tool; a bundle is more, not less. Building a plugin platform — installer,
sandbox, SDK, registry — is rejected: five products for one consumer, on the
evidence of three adopters. What remains is the smallest thing that makes a
third-party process tool's presence, footprint and output **governed**: known
to the journal, bounded by the gate, fed to the implementer, removable with
proof.

## Decision

### 1. An extension is a declared manifest, not code we run

An extension is a file `.agentmarshal/extensions/<name>.toml` in the governed
repository:

```toml
schema = 1
name = "openspec"
version = "<as installed>"          # informational; nothing pins it
footprint = ["openspec/", ".claude/commands/opsx/", ".claude/skills/",
             ".agents/skills/"]
documents = ["openspec/specs/"]                 # what brief feeds the implementer
artifacts = ["openspec/changes/archive/"]       # what completion may pin
install = "npx @fission-ai/openspec@latest init"  # recorded; run by the operator
remove  = "rm -rf openspec .claude/commands/opsx" # recorded; run by the operator
```

`footprint`, `documents` and `artifacts` entries use the scope syntax of
ADR-0003 and nothing more: an exact path, or a directory prefix ending in `/`.
There are no globs, because the gate's scope check has none, and one matcher
serving two purposes is the point of D2. Where a tool's files share a directory
with others (as OpenSpec's skills share `.claude/skills/`), the footprint names
the directory and the operator accepts that the whole directory is the
extension's to change under its tasks.

The manifest declares; AgentMarshal executes none of its strings. `install`
and `remove` are recorded so the operator's action is reproducible and so a
removal can be verified against `footprint`. Declarative over imperative: this
is the pre-commit shape (id, entry, files), not an SDK.

### 2. The footprint is scope, and the gate already enforces scope

Paths under an extension's `footprint` belong to that extension. A candidate
may change them only under a task whose contract names the extension
(`extensions = ["openspec"]`) or lists the paths in `scope` explicitly.
Otherwise they are "paths outside contract scope" — the refusal the gate has
printed since 0.1.0. No new check: the footprint joins the task's effective
scope when the contract names the extension, and stays outside it when it does
not.

Installing or removing an extension is therefore an ordinary task: its contract
names the extension, its scope is the footprint, the diff is reviewed and gated
like any change, and the completion is evidence that the process tooling
changed — when, by whom, under which review. There is no journal-only path for
it, because the footprint lies outside `.agentmarshal/`.

### 3. Named documents and decisions reach the implementer and the reviewer, and the gate checks the documents were touched

A contract may name `documents = [...]` in scope syntax (an extension's
`documents` join them when the contract names the extension) and
`decisions = ["ADR-0003", ...]`, the decisions the task serves or is bounded
by. `brief` includes the named documents' content and the named ADRs in the
implementer's context; the review prompt names both, so a reviewer may refuse
for contradicting a named decision and not only the contract. When a contract
names documents, the gate adds one line: `PASS: named documents touched
(<paths>)` when the candidate's diff changes at least one path under them, or
`FAIL: named documents untouched: <paths>` — a refusal, by the operator's
decision of 2026-09-06, because a warning here would be the request OpenSpec
already makes.

This is the OpenSpec discipline — change the spec with the code — made a
refusal instead of a request. It checks presence of a change, **not its
truth**: whether the spec now describes the system is the reviewer's job and
the operator's, exactly as with tests today.

A contract that names no documents adds no line: the diff-lane transcript
stays as it is today. The check exists only where it was asked for.

### 4. Nothing extension-defined runs inside the gate

The gate reads manifests and diffs. It never executes an extension's
`install`, `remove`, hooks or scripts, and no extension can add, remove or
alter a gate check. Extensions act at `open` (footprint into scope), `brief`
(documents into context) and `complete` (artifacts pinned) — all three are
either reads or journal writes under the operator's command. This keeps the
trust boundary proposal 009 was deferred to protect: the gate's decision
depends on the journal and the diff, not on third-party code.

### 5. Removal is verified, archival is a finding

`remove` is a task (D2). Its completion is refused while any `footprint` path
still exists in the candidate's tree — the manifest is the checklist, and the
check is a gate line; the manifest file itself is the last path to go and is
exempt from its own footprint. If the operator wants to keep what the tool produced, the removal
task records a `finding` (ADR-0009) whose artifacts are hash-pinned copies
under the journal: archived by content, provable later, and no longer in the
working tree.

### 6. What this establishes, and what it does not

It establishes that a process tool's presence, footprint, inputs to the
implementer and removal are recorded, bounded and checked. It does **not**
establish that the tool is safe (nothing is vetted; `install` runs whatever the
operator runs), that its output is true (see D3), that it is isolated (a
process tool writes into the repository — that is its purpose; the footprint
bounds where, the gate refuses elsewhere), or that any tool works without an
adapter (an interactive tool's commands become text in `brief`; someone writes
that text). "Plug and play" is not a phrase this ADR licenses.

Templates for a first extension (OpenSpec) ship only after this project has
run three to five of its own tasks with it. A second extension is written when
a second real user exists, not before.

## Consequences

- Contract header gains optional `extensions`, `documents`, `decisions`;
  `open` warns when scope touches `docs/adr/` and `decisions` is empty. The
  header `schema` moves to 2, and the parser accepts 1 and 2: a schema-1
  contract, or a schema-2 contract without the fields, reads and behaves
  exactly as today. The record schema is untouched. UPGRADING names the header
  change in one line, because `open` and `brief` start reading fields that did
  not exist.
- `brief` gains a section for named documents and decisions. The review prompt
  names them.
- One new gate line, only when `documents` is named; one new refusal in
  `complete` for removal tasks, only when the contract names an extension being
  removed.
- No new record type, no new CLI in the first cycle: manifests are written by
  hand, install/remove run by hand as tasks (D2). `extension add/remove`
  commands are decided after the dogfood, by its numbers (rounds, findings
  about spec–code mismatch, cost) — the sidecar task CR-003 pre-registers
  them.
- Downstream: docs/overview (contract header), quickstart (one paragraph),
  sidecar.md (the footprint is a host path; a sidecar contract may name it —
  the gate's scope check in a sidecar is advisory as everywhere else).

## Alternatives considered

- **Lifecycle hooks (proposal 009).** Rejected again for the same reason: code
  running at a gate boundary becomes something the gate trusts.
- **Bundle OpenSpec.** Rejected: the adopter wanted one tool; a bundle is two
  and a second toolchain, and we would own a moving third-party format.
- **Plugin SDK and registry.** Rejected: one consumer, five products, and a
  maintenance promise (track N young tools) we already fail at N=5 tripwires.
- **Harness-native plugins only** (skills and commands, no journal, no gate).
  Rejected as the whole answer: it installs and removes, but enforces nothing
  and records nothing — it is what the adopter already has. Kept as the
  delivery vehicle for harness assets inside a footprint.
- **A sandbox.** Rejected as a category error: bounding *where* a tool writes
  is scope; restricting *how* it runs is the harness's sandbox, not ours.
