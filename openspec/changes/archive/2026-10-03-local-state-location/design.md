## Context

ADR-0014's map of places puts `agentmarshal/` inside the git common directory —
`.git/agentmarshal/` in an ordinary clone — and decision 5 rules that in a
sidecar the tree is the **journal** repository's, never the host's. The code
that knows which repository the journal lives in already exists:
`resolve_placement` reads `project.json` and returns a `Placement` whose
`project_root` is the repository holding the journal in both placements (in a
sidecar the journal lives inside the sidecar's own tree), while `host_root` is
the sidecar's host. The code that asks git for the common directory also
exists: `_git_common_dir` in `project.py`, written so that two worktrees of
one repository report the same answer — which is exactly the property a linked
worktree needs here.

## Goals

- One function answers where local state lives, in every placement.
- The named locations — `log/`, `extensions/`, `deps/`, `trust.toml`,
  `switches.toml`, `plan.toml` — come from the same place, so no writer spells
  them itself.
- Resolving is pure; creating is a separate, explicit act.
- Failure names the repository and the cause.

## Non-Goals

- Writing anything at the location: the process log, trust, switches and plan
  files are later tasks. Nothing calls the module yet.
- `status`/`doctor` printing the paths (ADR-0014 decision 13 — a later task).
- The user-scope directories of ADR-0014's map (`~/.config/agentmarshal/`).

## Decisions

- **The input is the resolved `Placement`, not a path.** ADR-0014 decision 5
  is then structural rather than a caller's duty: the module asks git about
  `placement.project_root` — the repository the journal lives in, embedded or
  sidecar — and `host_root` never enters the call. A caller cannot get the
  sidecar case wrong because there is nothing to get wrong.
- **`_git_common_dir` is exposed as `git_common_dir` and given an honest
  contract.** It used to collapse every failure — git missing, not a
  worktree, undecodable output — into `None`, which is all
  `initialize_project`'s equality check needs. A location API needs the
  *cause*: the public contract mirrors `find_git_root`'s —
  `GitNotAvailableError` when git cannot run or answers something
  unreadable, an answer whose `path` is `None` when git runs but cannot
  name a common directory (no worktree), keeping git's own stderr in
  `reason` so a refusing caller quotes git instead of inventing a cause.
  `initialize_project`'s comparison is unchanged: it still asks whether
  the two answers are equal, `reason` takes no part in equality, and an
  indeterminate answer behaves exactly as a `None` did — two unanswered
  calls still compare equal and refuse with the old "worktree of host"
  wording, one unanswered call still passes silently. That indeterminacy
  is a known limitation of the init check, left as it was; `reason`
  exists for the callers that must name a cause, which is what local
  state needs.
- **Resolution returns a value object; creation is a second call.**
  `local_state(placement)` runs `git rev-parse` and returns a `LocalState` —
  the root plus the six named locations as paths. It creates nothing, so a
  reader can ask "where" without side effects. `ensure_directory(path)` is the
  explicit counterpart a writer calls for a directory location; the file
  locations are created by their writers when they write.
- **Failure is a `LocalStateError` naming the repository and the cause.** The
  module follows the codebase's per-module error convention
  (`PlacementError`, `SessionRecordError`): a clean message, not a bare
  `CalledProcessError` or a traceback.

## Risks

- [A project root that is not inside any git worktree] → `git rev-parse`
  fails; the caller gets a `LocalStateError` naming the path and git's reason.
- [A stale worktree (`.git` pointer moved)] → git itself reports the failure;
  same clean error path.
- [`ensure_directory` pointed at a file location] → caller error; the
  function is documented for directory locations and creates whatever it is
  given, like `mkdir -p`.
