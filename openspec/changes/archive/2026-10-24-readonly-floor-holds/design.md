## Context

CR-221's floor makes the `pre-gate` candidate read-only in the
stage's own child (`isolation.py`'s `_bind_read_only`, run as
`preexec_fn`): `MS_REC | MS_PRIVATE` on `/`, a self-bind of the
candidate, a `MS_BIND | MS_REMOUNT | MS_RDONLY` remount — and the
probe's throwaway child runs the same calls so its verdict matches
what a stage gets. Two defects surfaced in the 2026-10-24
reviewer-model test and were confirmed by experiment.

**The `EPERM` remount.** Mounts touched from inside a user
namespace carry locked flags — mount attributes a remount there
may not clear (mount_namespaces(7)). The remount passed only the
three flags, so a candidate under a `nosuid,nodev` mount — the
ordinary `/tmp` — answered `EPERM` and the floor reported not
enforced. `os.statvfs(directory).f_flag` already reports the
candidate mount's flags; the catch is that `ST_*` values are not
`MS_*` values (`ST_RELATIME` is 4096, `MS_RELATIME` is `1 << 21`),
so the flags ride on an explicit mapping, not on copying `f_flag`.

**The inherited working directory.** `Popen(cwd=snapshot)`
changes into the candidate before `preexec_fn` runs, so the cwd
the setup inherits was resolved before the bind and still names
the underlying writable mount — a relative write walked straight
past the read-only bind while an absolute one hit `EROFS`. A
`chdir` after the bind resolves the path against the new mount
table and lands on the read-only mount.

## Decisions

- **One mapping function, `_locked_mount_flags`.** It takes
  `f_flag` and answers the `MS_*` bits the remount must keep —
  the six flags the kernel locks: suid/dev/exec and the atime
  trio. Anything `f_flag` carries beyond them is not ours to
  keep. The constants live beside the existing `_MS_*` and
  `_CLONE_*` literals; `os.ST_*` carries them where Python does,
  and the literals keep the mapping honest elsewhere — the same
  pattern the namespace flags already use.

- **The statvfs read precedes the mounts.** The flags wanted are
  the candidate mount's own, so `f_flag` is read before the
  self-bind — a bind clone would only mirror them anyway.

- **The re-entry is inside `_bind_read_only`, after the remount.**
  `_bind_read_only` ends with `os.chdir(directory)`: the stage's
  setup calls it before the capability drop and `execve`, and the
  probe's `_probe_read_only` calls the same function, so the
  probe's answer keeps matching what a stage gets — one sequence,
  one place. A failure of the step is an `OSError` like a failed
  mount: the stage's report names `read-only candidate` not
  enforced with the reason and the stage still runs — never a
  silent weakening.

## Risks and trade-offs

- Where the remount now carries `relatime` and friends, the bind
  keeps them; clearing them was never the floor's business — the
  point is read-only, nothing more.
- A candidate on a mount reporting none of the six flags remounts
  with exactly the old flags: behaviour on a platform that
  enforced everything is unchanged.
- `os.chdir` in `preexec_fn` is as safe as the mounts are: no
  allocation, POSIX-only, and inside the one guarded block whose
  failures ride the report pipe — nothing escapes `preexec_fn`.
