## Why

CR-221's read-only floor has two defects the reviewer-model test of
2026-10-24 found and an experiment outside any sandbox confirmed.
In a user namespace the kernel refuses a remount that would clear a
flag locked on the original mount: the floor's
`MS_BIND | MS_REMOUNT | MS_RDONLY` remount fails `EPERM` on any
candidate under a `nosuid,nodev` mount — any `/tmp` — so the floor
reports not enforced where it could hold. And `Popen(cwd=…)`
changes directory before `preexec_fn`, so the child's working
directory still names the underlying writable mount: a relative
write bypasses the read-only bind entirely.

## What Changes

- The remount carries every mount flag
  `os.statvfs(directory).f_flag` reports that a user namespace may
  not clear — `ST_NOSUID` → `MS_NOSUID`, `ST_NODEV` → `MS_NODEV`,
  `ST_NOEXEC` → `MS_NOEXEC`, `ST_NOATIME` → `MS_NOATIME`,
  `ST_NODIRATIME` → `MS_NODIRATIME`, `ST_RELATIME` → `MS_RELATIME` —
  mapped by one function.
- After the remount, still before the capability drop and `execve`,
  the child changes its working directory to the candidate
  directory again (`os.chdir`), so a relative write meets the
  read-only bind; a failure of that step is reported on the
  read-only guarantee as not enforced, never silently.
- The run's probe performs the same remount and re-entry, so its
  answer matches what a stage gets.

## Capabilities

- modify: `extension-stages`

## Impact

On a platform that allows the floor — including a candidate under
`/tmp`'s `nosuid,nodev` mount — a stage cannot write the candidate
by any path, relative or absolute. Nothing else changes: result
lines, the note lines and every other stage behaviour are as
CR-221 left them; a platform enforcing everything shows unchanged
output.
