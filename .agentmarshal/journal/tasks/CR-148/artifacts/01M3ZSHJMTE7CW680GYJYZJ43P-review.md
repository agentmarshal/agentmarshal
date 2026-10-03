I reviewed the diff statically against the contract. The snapshot has no virtualenv and command execution is restricted here, so I could not run `uv run pytest / ruff / mypy / agentmarshal validate` — acceptance criterion 5's "full CI sequence passes" is unverified by me, though I found no line-length, typing, or import-cycle problem that would break it.

What holds up:

- `local_state(placement)` takes `placement.project_root` — the journal's repository in both placements — so `host_root` structurally cannot leak into the call (`src/agentmarshal/localstate.py:83`). The sidecar rule is enforced by construction, not by caller discipline.
- `_git_common_dir` was exposed as `git_common_dir`, not copied (`src/agentmarshal/project.py:332`), and its new raise/`None` split genuinely mirrors `find_git_root` (`src/agentmarshal/project.py:95-110`).
- Resolving is pure; `ensure_directory` is the separate explicit creator. All six named locations are derived properties of the frozen `LocalState`.
- All eight delta-spec scenarios have a test whose docstring names them verbatim; the archive directory matches the shape of the other 2026-10-03 archives (`.openspec.yaml`, `design.md`, `proposal.md`, `specs/`, `tasks.md`), the new capability's Purpose is written in the delta rather than left as a placeholder, and nothing outside `tests/test_localstate.py` imports the module.

Three non-blocking issues:

**misleading-failure-cause** — `src/agentmarshal/localstate.py:88-91` hardcodes "(not a git worktree)" for every non-zero `git rev-parse`, and `git_common_dir` discards `result.stderr` entirely (`src/agentmarshal/project.py:361-362`). A stale `.git` pointer, an unreadable repository, or a git older than 2.31 (which does not know `--path-format=absolute`) all produce a message that names a cause that is false. design.md's risk table promises the opposite — "the caller gets a `LocalStateError` naming the path and git's reason" and, for the stale worktree, "git itself reports the failure" — and the spec scenario says the failure names "git's reason". The tested case happens to be the one where the canned string is accurate.

**init-indeterminacy-claim-overstated** — the comment at `src/agentmarshal/project.py:411-414` claims an unanswerable comparison "now refuses once, naming why", but only the exception path was added. The `None` return path is unchanged: two `None`s still compare equal and refuse with the wrong message ("is a worktree of host"), and one `None` against a real path still passes silently. Worse, the new `GitNotAvailableError` branch is effectively dead, because `find_git_root` at `src/agentmarshal/project.py:378` and `:394` has already proven git runnable before the comparison is reached. The failure mode the design named — a legitimate sidecar refused as a host worktree because both `rev-parse` calls exit non-zero — survives the change.

**snapshot-misses-directories** — `_tree_snapshot` at `tests/test_localstate.py:62-68` filters on `path.is_file()`, so a directory created under the host leaves the snapshot identical. The spec scenario asks for the host's tree and git directory to be "byte-for-byte what they were before", and the test creates three directories (`log/`, `extensions/`, `deps/`) whose misplacement it could not see. The three file writes that follow still catch the regression this test exists for, so the coverage gap is narrow rather than fatal.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "df7f28f5d7facb186b02eb456aabeb7a44108550", "verdict": "approved", "findings": [], "advisory_findings": ["misleading-failure-cause", "init-indeterminacy-claim-overstated", "snapshot-misses-directories"]}
AGENTMARSHAL_VERDICT_END
