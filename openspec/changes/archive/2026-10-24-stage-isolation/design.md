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
`os.unshare`. A third fact came in review (F-ROOT-READONLY): the
capabilities a new user namespace grants survive `execve`, so the
bind's read-only-ness must outlive them — the child drops them all
before exec, for any uid. And the guarantees the kernel allows vary by
environment: unprivileged user namespaces may be refused outright,
and a `MS_BIND | MS_REMOUNT | MS_RDONLY` remount over a mount owned
by the initial user namespace fails `EPERM` under kernels that lock
such mounts. Both are ordinary, expected conditions — so the design
probes first and names whatever it cannot enforce rather than
discovering it in the stage's child or weakening silently.

## Decisions

- **One mechanism module.** `agentmarshal/isolation.py` holds the
  namespace/mount machinery: the `Probe` verdict, `probe()`, the
  `stage_setup(network=, readonly=, report_fd=)` factory returning
  the `preexec_fn`, and `parse_setup_report()` for the child's own
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

- **Every capability is dropped before exec, for every uid.** A new
  user namespace grants the child its full capability set, and
  `execve` does not take it back (user_namespaces(7)): a stage that
  kept it could remount the candidate read-write or unmount the
  bind — for a uid-0 run through the root exec rules, for any other
  uid through the caps the namespace itself granted. So last, after
  the mounts that need `CAP_SYS_ADMIN`, the child clears the ambient
  set (`prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL)`), sets and
  locks `SECBIT_NOROOT` and `SECBIT_NO_SETUID_FIXUP` plus
  `PR_SET_NO_NEW_PRIVS`, drops each bounding capability
  (`prctl(PR_CAPBSET_DROP, cap)`) up to
  `/proc/sys/kernel/cap_last_cap`, and clears effective, permitted
  and inheritable with `capset` (`_LINUX_CAPABILITY_VERSION_3`,
  last — the bounding drops need `CAP_SETPCAP`). All through ctypes
  libc — never a shell, never `PATH`. The drop runs whenever a user
  namespace was entered, whether the request was network,
  read-only or both; with no user namespace there is nothing to
  drop. The probe's throwaway child performs the same drop, so an
  "enforceable" verdict covers it.

- **A failed drop is named, not refused.** Of the two options —
  report `not enforced` or refuse the stage — this design reports:
  a drop failure is an environment refusal like a refused `unshare`,
  which the contract already answers with weaken-and-report, and the
  per-guarantee failure channel can carry it exactly. The child
  reports its failure on the child's dedicated pipe and the run
  notes `not enforced: <guarantee> (capabilities could not be
  dropped: <reason>)` on every guarantee the child was asked to
  enforce; the stage still runs. What is not done is an exec that
  keeps capabilities in silence.

- **Child failures are never silent — and never forgeable.** The
  child reports on a dedicated pipe the parent opens with
  `os.pipe()`: the write end is close-on-exec from creation (PEP
  446 makes `os.pipe()` descriptors non-inheritable) and is never
  named in `pass_fds` — `pass_fds` would clear the flag and keep
  it inheritable past `execve` — so the spawn's own descriptor
  sweep, which runs after `preexec_fn`, closes it before the
  stage's code runs and the extension never holds it. Still before
  exec the child writes one `<guarantee>=<ok|reason>` line per
  requested guarantee in a single write. The parent reads the pipe
  to EOF once `Popen`'s own exec handshake has already waited for
  the child to exec or die — the drain cannot block — and
  `parse_setup_report` names each reported failure; a guarantee
  the report does not name — a child that died before writing —
  cannot vouch for itself and is named not enforced the same way.
  The setup is one guarded block from its first line: whatever
  step fails is named in the report and the function returns, so
  the stage execs and runs unconfined for what failed — an
  exception escaping `preexec_fn` would be the parent's
  `SubprocessError`, a `not run` where a run and a name were owed
  (F-SETUP-CLOEXEC). The capability drop keeps its own rule
  inside: a failed drop names every guarantee the child was asked
  to enforce. This is how `subprocess` itself reports exec
  failures; nothing in the stage's own output is ever read as a
  core message, so a line shaped like a report that a stage prints
  is framed as its output and decides nothing — the round-1 marker
  channel through the captured stream was forgeable exactly here.

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
