## 1. One helper asks git

- [x] 1.1 `git_common_dir` is exposed from `project.py` — `GitNotAvailableError`
  when git cannot run or answers unreadably, `None` when git cannot name a
  common directory — and `initialize_project` compares through it, still
  refusing a sidecar whose relation to the host cannot be determined —
  verify: grep finds one helper; the worktree-of-host init test still passes.

## 2. The location

- [x] 2.1 `local_state(placement)` in `localstate.py` returns
  `<git common directory>/agentmarshal/` for the repository holding the
  project's journal — verify: test on an embedded project.
- [x] 2.2 The six named locations are exposed under the root: `log/`,
  `extensions/`, `deps/`, `trust.toml`, `switches.toml`, `plan.toml` —
  verify: test.
- [x] 2.3 A linked worktree resolves to the same root as the main checkout —
  verify: test with `git worktree add`.
- [x] 2.4 In a sidecar the root is the journal repository's common directory,
  never the host's — verify: test snapshots the host's working tree and git
  directory across resolving and creating every named location.

## 3. Resolving is not creating

- [x] 3.1 Resolving creates nothing; `ensure_directory` creates a directory
  location explicitly — verify: test asserts nothing exists after resolve,
  the directory exists after the call.
- [x] 3.2 Where git cannot name the common directory the call raises
  `LocalStateError` naming the repository and the cause — verify: test on a
  project outside git.
