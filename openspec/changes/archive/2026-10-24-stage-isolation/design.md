## Context

`stage run` launches each stage's `command` as
`[sys.executable, <bin/>]` via `subprocess.Popen`, with the candidate
snapshot as `cwd` and `_stage_env` building the environment —
minimal `PATH`, the names `isolation.env` declares, the five
protocol variables last. ADR-0013 decision 8's isolation is declared
in `journal/extensions.py`'s `ExtensionIsolation` (`network`,
`env`, `writes`, `timeout_seconds`) but, before this change, only
`env` and the timeout had effect.

Two platform facts shape the design. A `uid_map`/`gid_map` write is
permitted only after `fork` and before `execve` — which is why the
setup must be a `preexec_fn`, never a wrapper process or a shell —
and inside a new user namespace `os.getuid()` already answers the
overflow id, so the caller's uid/gid must be captured before
`os.unshare`. And the guarantees the kernel allows vary by
environment: unprivileged user namespaces may be refused outright,
and a `MS_BIND | MS_REMOUNT | MS_RDONLY` remount over a mount owned
by the initial user namespace fails `EPERM` under kernels that lock
such mounts. Both are ordinary, expected conditions — so the design
probes first and names whatever it cannot enforce rather than
discovering it in the stage's child or weakening silently.

## Decisions

- **One mechanism module.** `agentmarshal/isolation.py` holds the
  namespace/mount machinery: the `Probe` verdict, `probe()`, the
  `stage_setup(network=, readonly=)` factory returning the
  `preexec_fn`, and `strip_failure_reports()` for the child's own
  reports. `stages.py` keeps the run's policy.

- **The probe runs in a throwaway `os.fork` child, never exec'd.**
  The child runs the real sequence — the unshares, the identity
  maps, the private-propagation and read-only bind against a
  temporary directory — and reports each guarantee's verdict over a
  pipe; it dies taking the namespaces with it. A child that cannot
  fork, dies or does not report is itself the reason both
  guarantees are named not enforceable. Non-Linux platforms and
  Pythons without `os.unshare`/`os.fork` answer without a child.
  The verdict is cached for the run — one probe however many stages
  are planned.

- **`preexec_fn`, decomposed on refusal.** `stage_setup` returns a
  closure the stage's child runs between `fork` and `exec`: one
  `os.unshare(CLONE_NEWUSER | CLONE_NEWNET [| CLONE_NEWNS])` as the
  contract prescribes, `deny` to `/proc/self/setgroups`, the
  one-line identity maps, then `mount(NULL, "/", NULL,
  MS_REC | MS_PRIVATE)` through ctypes libc `mount` and the
  self-bind remounted read-only. A refused combined `unshare` is
  retried per guarantee — a network namespace the kernel allows
  must not go unmade because the mount namespace was refused, and
  each guarantee must name its own reason.

- **Child failures are never silent.** Every requested guarantee a
  setup step fails is written to the child's stderr as
  `AGENTMARSHAL-SETUP-FAILED: <guarantee>: <reason>` — the first
  bytes of the captured output, since they precede exec — and the
  setup never raises out of the child. `strip_failure_reports`
  removes those lines from the stream the run reframes and the
  guarantees they name join the probe's own `not enforced` set;
  the stage still runs.

- **The note line is the stage's own.** Each stage owed a guarantee
  it did not get gets one `stage run: note: <name>: not enforced:
  <guarantee> (<reason>); …` line on stderr, next to its result
  line — the style of the existing `PATH is fixed by the core`
  note. A guarantee enforced is not mentioned, so on a platform
  enforcing everything output is unchanged. A stage that does not
  run carries no isolation note.

- **`writes` is reported, not faked.** The mount namespace covers
  the candidate directory alone; anything a stage writes outside
  it — the process log aside, which the declared value names — has
  no enforcement in this mechanism. A manifest declaring
  `isolation.writes` therefore always earns `not enforced: writes
  beyond the candidate (the core has no filesystem sandbox beyond
  the candidate)` rather than implying a sandbox that does not
  exist.

- **Provider secrets are the pre-gate floor, decided by name.** The
  fixed list (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
  `GITHUB_TOKEN`, `GH_TOKEN`, `GITLAB_TOKEN`) plus the suffixes
  `_API_KEY`, `_TOKEN`, `_SECRET`, `_PASSWORD` are withheld in
  `_stage_env` when `phase == "pre-gate"`, however the manifest
  declares them, and the withheld declared names are noted once on
  stderr before the stages run. `post-gate` passes declared names
  as before — the floor is the pre-gate's alone.

## Risks and trade-offs

- `preexec_fn` is POSIX-only and runs before Python's interpreter is
  safe in the child; the setup does no allocation beyond small
  writes, matching the documented caveats. Non-POSIX platforms get
  the probe's `not Linux` verdict and run with the guarantees
  named.
- The read-only bind cannot cover every filesystem a stage sees —
  only the candidate is the contract's floor — which is why
  `writes` is named rather than implied.
- A stage run inside an environment that forbids namespaces loses
  the guarantees but keeps the run and the honest note; the forced
  -probe tests cover every branch without needing kernel support.
