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
footprint = ["openspec/", ".claude/commands/opsx/",
             ".claude/skills/openspec-propose/", ".agents/skills/openspec-propose/",
             # ... one entry per skill directory the tool installs
            ]
documents = ["openspec/specs/"]                 # what brief feeds the implementer
artifacts = ["openspec/changes/archive/"]       # what completion may pin
install = "npx @fission-ai/openspec@<version> init"  # recorded; run by the operator
remove  = "rm -rf openspec .claude/commands/opsx .claude/skills/openspec-* .agents/skills/openspec-*"
```

`footprint`, `documents` and `artifacts` entries use the syntax the gate's
scope matcher accepts (ADR-0003 names the rule `diff ⊆ scope`; the matcher,
in the gate since its first release, accepts an exact path or a directory
prefix ending in `/`) and nothing more. There are no globs, because the scope check has none, and one
matcher serving two purposes is the point of D2. Where a tool's files share a directory
with others (as OpenSpec's skills share `.claude/skills/`), the footprint lists
the tool's own entries one by one; a footprint never claims a directory it
shares. The `install` and `remove` strings are opaque to AgentMarshal and may
use whatever the operator's shell understands.

The manifest declares; AgentMarshal executes none of its strings. `install`
and `remove` are the operator's declaration of what was run, recorded so a
later reader knows what was claimed and so a removal can be checked against
`footprint`. AgentMarshal does not attest the declaration: it does not verify
that the command ran, succeeded, or produced the files the footprint names.
Nothing pins the tool's version either; a manifest that records `@latest`
records exactly that much. Declarative over imperative: this
is the pre-commit shape (id, entry, files), not an SDK.

### 2. The footprint is scope, and the gate already enforces scope

Paths under an extension's `footprint` belong to that extension. A candidate
may change them only under a task whose contract names the extension
(`extensions = ["openspec"]`) or lists the paths in `scope` explicitly.
Otherwise they are "paths outside contract scope" — the refusal the gate has
printed since 0.1.0. No new check: the footprint joins the task's effective
scope when the contract names the extension, and stays outside it when it does
not.

The gate reads a manifest where it reads the contract: from the base side of
the history the candidate belongs to — the trusted-input rule ADR-0006,
ADR-0008 and ADR-0009 each restate — and in a sidecar from the sidecar working
tree (ADR-0008). A candidate that edits a manifest changes what the *next*
task's gate reads, not its own; it cannot widen its own scope or silence a
documents check by rewriting the manifest it ships with.

A change that touches only a manifest is **not** a journal-only transaction.
The deterministic lane is keyed on `.agentmarshal/journal/`, the records — and
`.agentmarshal/extensions/` lies outside it, so a manifest-only change already
takes the review-bound diff lane, under a contract whose scope names the
manifest path. That is the right outcome and this ADR fixes it as intended: a
manifest decides what the gate reads next; it is configuration, and
configuration is reviewed. Placing manifests under `.agentmarshal/journal/`
would have put them on the unreviewed lane, and is therefore ruled out.

Installing or removing an extension is therefore an ordinary task whose
contract names the manifest's own path `.agentmarshal/extensions/<name>.toml`
explicitly, because a footprint does not contain it. An install task lists the
footprint paths explicitly as well: no manifest exists on the base side yet
for `extensions = [...]` to resolve. A removal task may name the extension —
the base still holds its manifest — and add only the manifest path. The diff is
reviewed and gated like any change, and the completion is evidence that the
process tooling changed — when, by whom, under which review. There is no
journal-only path for it, because the footprint lies outside `.agentmarshal/`.

### 3. Named documents and decisions reach implementer and reviewer, and the gate checks them

A contract may name `documents = [...]` in scope syntax (an extension's
`documents` join them when the contract names the extension) and
`decisions = ["ADR-0003", ...]`, the decisions the task serves or is bounded
by. `brief` includes the named documents' content and the named ADRs in the
implementer's context, and the review prompt names both; how the reviewer is
asked to use them is the implementation task's to word. When a contract
names documents, the gate adds one line: `PASS: named documents touched
(<paths>)` when the candidate's diff changes at least one path under them, or
`FAIL: named documents untouched: <paths>` — a refusal, by the operator's
decision of 2026-09-06, because a warning here would be the request OpenSpec
already makes.

The line belongs to the diff lane, where there is a candidate diff to examine.
A journal-only transaction and the findings lane (ADR-0009) have none; there
the line reads `NOT EXAMINED: named documents (no candidate diff)`, in the
manner ADR-0009 D3 uses for the checks its lane cannot run.

This is the OpenSpec discipline — change the spec with the code — made a
refusal instead of a request. It checks presence of a change, **not its
truth**: whether the spec now describes the system is the reviewer's job and
the operator's, exactly as with tests today.

A contract that names no documents adds no line: the diff-lane transcript
stays as it is today. The check exists only where it was asked for.

### 4. Nothing extension-defined runs inside the gate

Four commands read manifests, and only read them: `open` reads them to
compute a task's effective scope from `extensions`; `brief` reads them for the
documents it feeds the implementer; `complete` reads them for the artifacts it
may pin and for the removal check (D5); `gate` reads them for scope (D2) and
for the documents line (D3). None executes an extension's `install`, `remove`,
hooks or scripts, and no extension can add, remove or alter a gate check. What
extensions change is inputs — scope, context, artifacts — under the operator's
command, never the decision procedure. This keeps the
trust boundary proposal 009 was deferred to protect: the gate's decision
depends on the journal and the diff, not on third-party code.

### 5. Removal is verified, archival is a finding

`remove` is a task (D2). Its completion is refused while a `footprint` path of
the base-side manifest still exists in the candidate's tree — the manifest is
the checklist, read from the side the candidate cannot edit, and the check is
a gate line. The candidate deletes the manifest itself along with the
footprint; the base still holds it for the check. If the operator wants to
keep what the tool produced, the removal
task records a `finding` (ADR-0009) whose artifacts are hash-pinned copies
under the journal: archived by content, provable later, and no longer in the
working tree.

### 6. What this establishes, and what it does not

It establishes that a declared footprint is bounded by the gate, that named
documents reach the implementer and are checked for change, and that a
removal is verified against the base-side manifest. A manifest's presence
records a declaration — that a tool was said to be installed with those
strings — not that the command ran, succeeded, or produced those files. It does **not**
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

- Contract header gains optional `extensions`, `documents`, `decisions`. The
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
  about spec–code mismatch, cost), which a research task in the operator's
  own journal pre-registers before the first data point.
- No change to the journal-only lane: `.agentmarshal/extensions/` lies outside
  `.agentmarshal/journal/`, so a manifest-only change already takes the diff
  lane and needs a review (D2).
- Downstream: docs/overview (contract header), quickstart (one paragraph),
  sidecar.md (the footprint is a host path; a sidecar contract may name it —
  the gate's scope check there is advisory, as every sidecar check is —
  ADR-0008 D5).

## Alternatives considered

- **Lifecycle hooks (proposal 009).** Rejected again for the same reason: code
  running at a gate boundary becomes something the gate trusts.
- **Bundle OpenSpec.** Rejected: the adopter wanted one tool; a bundle is two
  and a second toolchain, and we would own a moving third-party format.
- **Plugin SDK and registry.** Rejected: one consumer, five products, and a
  maintenance promise — track N young tools, re-scanned before each release —
  of a kind this project has already failed to keep for a shorter list of
  neighbours.
- **Harness-native plugins only** (skills and commands, no journal, no gate).
  Rejected as the whole answer: it installs and removes, but enforces nothing
  and records nothing — it is what the adopter already has. Kept as the
  delivery vehicle for harness assets inside a footprint.
- **A sandbox.** Rejected as a category error: bounding *where* a tool writes
  is scope; restricting *how* it runs is the harness's sandbox, not ours.
