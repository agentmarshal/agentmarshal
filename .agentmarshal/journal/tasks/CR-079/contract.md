+++
schema = 1
id = "CR-079"
title = "A journal can sit beside its repository: sidecar configuration and host resolution"
scope = ["src/agentmarshal/project.py", "src/agentmarshal/journal/placement.py", "src/agentmarshal/journal/open_task.py", "src/agentmarshal/journal/review.py", "src/agentmarshal/cli.py", "tests/test_placement.py", "tests/test_journal.py"]
acceptance = [
  "`agentmarshal init --host <path>` initializes a sidecar journal: project.json carries the placement and the host path, and the host repository is verified to be a git worktree at init time",
  "a project.json without a placement key is an embedded journal, so every existing project keeps working unchanged",
  "a placement resolver gives commands two roots: where the journal lives and where git facts come from; embedded resolves both to the project root",
  "in a sidecar, `open`'s scope warnings check paths against the host worktree, and `review` snapshots the host repository",
  "journal commands work in a sidecar: open, brief, status, report, amend, reopen, abandon, submit-review, review, accept, record-session, validate, prune",
  "`gate` and `complete` refuse to run in a sidecar placement, naming the reason: the advisory mode is a following task, and until it exists refusing is the honest answer",
  "no command ever writes anything into the host repository or its worktree, and a test demonstrates the host tree is byte-identical after a full sidecar session",
  "a sidecar with a missing or non-git host path fails with the path and the reason, at the first command that needs the host, not with a traceback",
]
+++

# CR-079: A journal can sit beside its repository — sidecar configuration and host resolution

## Context

ADR-0008 decided that placement is a property of a journal: **embedded** (in
the governed repository, today's default, untouched) and **sidecar** (the same
journal in a repository of its own, naming one host repository it records
evidence about). The two personas it serves are decided there too: an operator
whose working evidence is private, and a practitioner who cannot install
anything into the repository they work in.

This task is the first implementation slice: configuration and root
resolution. Today every command conflates two roots that happen to coincide —
where the journal lives, and where git facts come from (resolving a commit,
snapshotting a tree, listing a commit's writers, checking a scope entry
against disk). A sidecar is precisely the case where they differ.

The advisory gate is deliberately **not** in this slice. Until it exists, a
gate run in a sidecar would either lie about its authority or improvise its
labelling; refusing with a named reason is the honest intermediate state, and
the refusal is testable.

## Objective

Let `init` create a sidecar journal, give every command the two roots, and
prove the host is never written.

## Acceptance Criteria

- `agentmarshal init --host <path>` initializes a **sidecar** journal in the
  current repository: `project.json` carries the placement and the host path,
  and init verifies the host is a git worktree, failing with the path and
  reason otherwise.
- A `project.json` without a placement key is an **embedded** journal. Every
  existing project keeps working with no change of any kind.
- A resolver in one place gives commands both roots — journal root and host
  root. Embedded: both are the project root. Sidecar: the journal stays under
  the project root, git facts come from the configured host.
- In a sidecar, `open`'s scope warnings check entries against the **host**
  worktree, and `review` snapshots the **host** repository.
- The journal-side commands all work in a sidecar: open, brief, status,
  report, amend, reopen, abandon, submit-review, review, accept,
  record-session, validate, prune.
- `gate` and `complete` **refuse** in a sidecar placement with a message
  naming why: the advisory mode lands in a following task, and until then a
  gate that ran would misstate its authority.
- **No command writes into the host.** A test runs a full sidecar session —
  init, open, review, accept, record-session, status, report — against a host
  fixture and asserts the host tree is byte-identical before and after
  (`git status --porcelain` empty and untracked listing unchanged).
- A missing or non-git host path fails at the first command that needs the
  host, with the path and the reason, never a traceback.

## Threat model and boundaries

The hazard of this slice is **writing where we promised never to write**.
ADR-0008 Decision 3 is absolute: the host carries no reference to, and no
marker of the existence of, any sidecar. One stray file, lockfile, or
gitignore entry written into the host worktree breaks the promise for every
private-journal adopter at once. That is why "host tree byte-identical" is an
acceptance criterion with a test, not a code-review hope, and why git commands
against the host must be read-only ones.

The host path in `project.json` is **operator configuration in the operator's
own private repository** — the same trust class as the rest of `project.json`
(ADR-0005's reasoning for `capture`, restated in `capture.py`'s docstring).
The following are therefore **not** defects in this task and must not be
guarded against:

- symlinks, traversal or TOCTOU on the configured host path — the operator
  names their own repository; following what they configured is doing what
  they asked;
- a hostile host repository — the sidecar's owner chose it; reading it is the
  point; and the reading is the same read-only git usage every embedded
  command already performs;
- concurrent modification of the host while a command runs — git's own
  behaviour is the answer, as decided for prune (CR-059).

## Non-Goals

- **The advisory gate and placement labelling on surfaces** — the next task.
  Here gate and complete refuse.
- Multi-host journals (ADR-0008 names them future work).
- Any sync/hosting story for a shared sidecar — it is a git repository.
- Migration between placements.
- Documentation beyond command help text — the second install-and-operate
  path is its own task, written after the dogfood.
