# ADR-0013: Extensions — stages, scopes, isolation, trust, switches, records

Status: Accepted
Date: 2026-10-03

Builds on [ADR-0007](ADR-0007-operator-acceptance.md) (operator acceptance
over the blocking findings of a non-approving review),
[ADR-0010](ADR-0010-process-extensions.md) (process extensions with a
declared footprint) and
[ADR-0012](ADR-0012-what-the-tool-does-and-what-it-supplies.md) (an extension
may drive the process), and on a separate decision on where local state lives.
**It partly revisits ADR-0010 and ADR-0007.** In ADR-0010: the refusal of
lifecycle hooks is lifted; the refusal of an installer stands; and the shared
switches file is excepted from "configuration is reviewed" — it alone changes
without review, while a manifest still takes the diff lane with review. In
ADR-0007: an acceptance stood only over the blocking findings of a
non-approving review; here it also covers an extension pause, which raises no
review finding, and an operational CR, which has no review at all. It answers
[proposal 009](../proposals/009-lifecycle-extension-points.md).

This ADR records a decision. The stages, manifest fields, commands, lanes and
directories it describes are **not implemented by this document**; they follow
in their own tasks. The present tense below is how a decision is written, not a
claim about shipped behaviour.

## Context

ADR-0010 gave an extension a declared footprint and refused hooks: a hook that
runs during the gate blurs what the gate trusts, and a hook interface is easy
to add and hard to remove. ADR-0012 lets an extension drive the process. What
remains to be said is where an extension is invoked, what it may do, where its
code lives, how it is checked that what runs is what was approved, how it is
switched on and off — and why none of this touches what the gate trusts.

A task's states are `open`, `done`, `abandoned`; the transitions are
`complete`, `abandon`, `reopen`; inside `open` there are events that change no
state — amendment, review, acceptance, session, finding. The merge itself is
made not by the tool but by the provider; the gate — the merge authority —
decides and never merges. The gate runs in CI, at the merge step — the host's
merge wrapper — before the merge, and inside `complete`, which may run before
or after the implementation merges.

## Decision

### A. When an extension runs

1. **An extension has one obligation** — to be invoked at its declared stage.
   The rest — writing to the journal, writing to the process log, pausing the
   process — are capabilities that depend on the stage, the scope and the
   isolation.
2. **Two stages to start:** `pre-gate` (in CI and at the merge step, before
   the gate) and `post-gate` (after `complete`). Inside `complete` — which
   may run before or after the implementation merges — a `pre-gate-stop`
   pause applies while the candidate is not yet merged into the target
   branch, and is reported as a warning once it is.
3. **The rule for future stages:** a hook before a transition may only pause
   the process; a hook after a transition may only notify and write to the
   log. New stages are added at an adopter's request; the candidates, each
   with its condition: "before review launch" — once a loss of quota on
   candidates known to be unfit is demonstrated; "after open" — if a supplied
   extension needs to create a scaffold when a task opens.
4. **The mode sits in the manifest:** `post-gate` — a notification, and a fix
   arrives only as a new CR; `pre-gate-warn` — a loud warning;
   `pre-gate-stop` — a pause, and an extension's own failure pauses too.
   There is no shared blocking key: the manifest is the adopter's
   declaration, and the mode in it is the policy.
5. **An extension is a separate step before the gate, not part of the gate.**
   The gate reads neither an extension's output nor its flags; its decision
   does not depend on whether extensions are installed at all. An extension's
   stop is a pause of the process before the gate; sorting it out — a fix in
   a new round, or operator acceptance — does not touch the gate. Acceptance
   here is the first of two extensions of ADR-0007: a pause raises no review
   finding, so the acceptance stands over the pause itself rather than over a
   non-approving review's blocking findings. The merge happens when the gate
   has passed and no pause stands. An extension cannot push through what the
   gate refused — by construction.
6. **Read from the base.** Manifests, modes, isolation, shared switches **and
   the code of shared extensions** are taken from the base commit; a pull
   request cannot weaken them for itself, tailor the check code to itself, or
   gain pause rights for an extension it adds itself.
7. **No silence.** Every extension gets a result line: checked / failed
   (reason) / addressee not found / did not finish (timeout) / switched off
   (by whom and why) / not run (changed after approval, dependencies do not
   match the lock). An extension's output goes in its own frame with a
   prefix, so it does not look like a gate line.

### B. Isolation

8. **Isolation is declared in the manifest** for any stage: network,
   environment variables by name, where the extension writes, timeout. For
   `pre-gate` there is a floor the manifest cannot remove: the candidate
   snapshot is read-only, no provider secrets, the timeout no higher than the
   core's limit. Network is allowed when declared and approved. The core
   enforces what is declared as far as the platform allows, and names in its
   output what it cannot enforce.

### C. Where an extension lives and who sees it

9. **An extension with commands is a directory** (`manifest.toml`; `bin/` —
   everything runnable; `lock/` — the dependency lock with hashes, if there
   are dependencies). An extension without commands — a declared footprint
   only — stays a single `<name>.toml` file, as in ADR-0010.

   | Scope | Extension directory | Dependencies installed to | Seen by |
   |---|---|---|---|
   | shared | `.agentmarshal/extensions/<name>/`, committed | `.git/agentmarshal/deps/<name>/` — from the lock, on each machine and in CI | everyone, and CI |
   | personal, in the clone | `.git/agentmarshal/extensions/<name>/` | `.git/agentmarshal/deps/<name>/` | one developer, all their worktrees |
   | user | `~/.config/agentmarshal/extensions/<name>/` (Windows: `%APPDATA%\agentmarshal\extensions\`) | `~/.local/share/agentmarshal/deps/<name>/` | one developer, all their repositories |

   The personal scopes only add extensions; they change nothing about the
   shared ones' modes, isolation or switches. The first release that ships
   this carries the shared and the personal-in-clone scopes; the user scope
   arrives when an adopter asks.

   | | shared | personal |
   |---|---|---|
   | invoked at its stage | yes | yes |
   | writes to the process log | yes | yes |
   | writes `ext` records to the shared journal | yes | no |
   | pauses the server-side process (CI, the merge step) | yes (`pre-gate-stop`) | no |
   | pauses a local run | yes | yes, marked "personal" |
   | post-gate | on the workstation and in CI | on the workstation only |

10. **A personal extension has no footprint in the repository:** its manifest
    carries no `footprint`, `documents` or `artifacts`; it writes neither to
    the working tree nor to the journal — only to the process log and to its
    own state under `.git/agentmarshal/`. `doctor` refuses a personal
    manifest that declares a footprint.
11. **Local state lives outside the working tree.** Personal extensions,
    dependencies, local grants and switches live in `.git/agentmarshal/`, the
    location the separate decision on where local state lives defines: shared
    by all worktrees, never committed. **The implementer-launch template in
    the adopter kit (ADR-0012) runs the executor with no write access to
    `.git/agentmarshal/` and `~/.config/agentmarshal/`** — otherwise a
    managed agent could switch off the extension that checks it, grant itself
    a shared one, or plant a personal one.

### D. Installation and trust: what runs is what was approved

12. **The tool does not perform installation** (as in ADR-0010). A shared
    extension is installed by an ordinary task: its directory is committed. A
    personal one is a directory under `.git/agentmarshal/extensions/`.
    External dependencies come **only from a lock with hashes**, installed by
    the ecosystem with verification (`npm ci`, `uv sync --locked`); no lock,
    no dependencies. `doctor` compares the installed dependencies with the
    lock. Changing what is installed happens only through new directory
    content.
13. **`command` names only a file in the `bin/` of its own directory.** `PATH`
    lookup is forbidden; an external tool is invoked through a `bin/`
    launcher and comes only from dependencies installed from the lock.
14. **A local grant covers the hash of the whole directory** — the manifest,
    `bin/`, the lock: `agentmarshal extension trust | untrust | list`. A
    shared extension with a command runs on a workstation only under a valid
    grant; in CI no grant is needed. **Before each run** the core recomputes
    the directory hash: on a mismatch the stage does not run, and the line
    reads `changed after approval: <file>`. Whether the dependencies still
    match the lock between install and run is `doctor`'s check, not every
    run's.
15. **The threat model for local state.** The hash check catches accidental
    changes and the executor in its sandbox. It does not protect against an
    agent or a process running with the user's rights and no sandbox: such a
    process rewrites both the extension and the grants file. The security
    rests on two things: **(a) the invariant — a personal extension has no
    authority**: it does not write to the journal and does not affect the
    server-side process or the gate, so a substituted personal extension can
    produce only a false local pause, a switched-off personal check, or a lie
    in the process log — evidence and the merge decision do not suffer, and
    giving a personal extension authority takes a new ADR; **(b) the executor
    sandbox** (Decision 11). Shared extension code at `pre-gate` runs from
    the base — it passed review and the provider protects it — so a forged
    local grant merely removes the question put to the developer before code
    the process already approved runs.

### E. Switches

16. **Switches live apart from the manifest** — switching off changes neither
    the extension directory nor the grants:
    - a personal extension is switched off by a flag for one run
      (`--skip-ext <name>`) or until re-enabled (`agentmarshal extension
      disable <name>`, a record in `.git/agentmarshal/switches.toml`);
    - a shared one — **only by an operational CR**: neither a flag nor a
      local setting can switch it off for a run.
17. **An operational CR is a gate lane of its own**, next to the journal one:
    the diff touches only `.agentmarshal/switches.toml` (name →
    on/off, reason) and its own task's records; no review is required — the
    one file excepted from ADR-0010's rule that configuration is reviewed,
    while a manifest still takes the diff lane with review;
    extensions' `pre-gate` stages do not run on it — otherwise a broken
    extension blocks its own switching off; the reason is mandatory; `status`
    and `doctor` show "switched off since CR so-and-so, reason". An adopter
    may require operator acceptance for an operational CR instead of the fast
    lane — the second extension of ADR-0007: an operational CR carries no
    review at all. It is opened with one command: `agentmarshal extension
    switch off <name> --reason "…"`.

### F. Records and overview

18. **Extension records are a shared `ext` type.** The core knows the
    envelope — the task, who, when, the commit, `schema`, `tool_version`; the
    kind carries a namespace and a version and is declared in the manifest;
    the body is opaque to the core, hash-pinned and size-limited. `validate`
    checks the envelope; a kind no manifest declares draws a warning —
    "addressee not found", not a refusal. What the body means is for the
    extension itself to check. Only a shared extension may write `ext`. The
    envelope's schema is decided separately.
19. `doctor` lists the active extensions by scope: mode; isolation declared
    and enforced; the grant (hash, when granted); whether the directory
    matches the approved one; dependencies against the lock; the switch.
    Grant changes are written to the process log.

### Manifest form (an example, not a template)

```toml
# .agentmarshal/extensions/openspec/manifest.toml
schema = 2
name = "openspec"
version = "1.13.2"
footprint = ["openspec/", "..."]       # a personal one has none
documents = ["openspec/specs/"]

[[stage]]
phase = "pre-gate-stop"                # post-gate | pre-gate-warn | pre-gate-stop
command = "bin/validate"               # only from this directory's bin/

[dependencies]
lock = "lock/package-lock.json"        # package hashes; installed by the ecosystem

[records]
kinds = ["openspec/change-archived@1"] # ext kinds; a personal one has none

[isolation]
network = false
env = []                               # variable names; no provider secrets at pre-gate
writes = "none"                        # none | process-log (on a workstation; CI has no process log)
timeout_seconds = 120
```

The full template with defaults, the schema and manifest validation are
implementation work.

## Left open

A thin installer (`extension add | remove | upgrade`: show the directory,
install dependencies from the lock, place it into the scope). The sign:
adopters ask to automate installation, or manual install errors surface in
findings.

## Consequences

- [proposal 009](../proposals/009-lifecycle-extension-points.md) gets its
  answer: stages exist; a pause lands before the gate, and the gate takes
  nothing from extensions.
- The stage interface is a promise for years, so it is minimal: in — a commit
  and a snapshot; out — "pause / no" plus text.
- ADR-0010's refusal of an installer stands; approval, the directory-hash
  check, the dependency lock and switches are added.
- Operator acceptance extends from review findings to extension pauses.
- The gate gains another lane — operational — alongside the regular, journal
  and findings
  ([ADR-0009](ADR-0009-research-findings-lifecycle.md)) lanes.
- Switching off a shared check becomes easy, but not silent.
- A "paused for me, not for my colleague" divergence is possible with
  personal extensions, and is always marked.
- The local protection is honestly bounded: running an agent without a
  sandbox removes it, and the top-level documentation says so next to the map
  of places.

## Alternatives considered

**A shared `extensions.blocking` key.** Unnecessary: the manifest is the
adopter's declaration, and the mode in it is the policy.

**Extension code inside the gate's process.** Rejected.

**A network ban at `pre-gate`.** Rejected: the gate takes nothing from an
extension; the network is a question of isolation and approval.

**Named isolation levels.** Rejected in favour of an explicit list.

**Hooks at every transition.** No request.

**A grant on the hash of the manifest alone.** Would have approved the
declaration while anything on `PATH` executed.

**A switch inside the manifest itself.** Would have reset grants.

**Local state in `.agentmarshal/local/` under `.gitignore`.** Per-worktree,
deleted with it, writable by the executor, protected by a single line.

**Signing the local state with a key from the OS keychain.** An agent under
the same user usually has access to it; complexity without protection.

**`ext` records from personal extensions.** Would clutter the shared journal.
