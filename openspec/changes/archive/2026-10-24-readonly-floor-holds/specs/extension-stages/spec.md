# extension-stages Specification (delta)

## MODIFIED Requirements

### Requirement: a pre-gate stage's candidate is bound read-only over itself

At `pre-gate`, the stage's candidate working directory SHALL be
read-only to the stage: in the same child, in a new mount
namespace, `mount(NULL, "/", NULL, MS_REC | MS_PRIVATE)` makes
propagation private, a bind mounts the candidate directory onto
itself and a `MS_BIND | MS_REMOUNT | MS_RDONLY` remount turns the
bind read-only — the remount carrying besides the mount flags the
candidate's own mount already holds that a user namespace may not
clear, `nosuid`, `nodev`, `noexec` and the atime flags `noatime`,
`nodiratime` and `relatime` as `os.statvfs(directory).f_flag`
reports them, each `ST_*` bit mapped to its `MS_*` counterpart
(`ST_NOSUID` to `MS_NOSUID`, `ST_NODEV` to `MS_NODEV`, `ST_NOEXEC`
to `MS_NOEXEC`, `ST_NOATIME` to `MS_NOATIME`, `ST_NODIRATIME` to
`MS_NODIRATIME`, `ST_RELATIME` to `MS_RELATIME`), so a candidate
under a `nosuid,nodev` mount such as `/tmp` becomes read-only
rather than refused with `EPERM` — the mounts made by libc's
`mount` through the core, and nothing outside the candidate
directory made read-only — and the network requirement's
capability drop, performed in the same child before `execve`, is
what keeps the stage itself from remounting or unmounting the bind
it was handed. After the remount, still before the capability drop
and `execve`, the child SHALL change its working directory to the
candidate directory again: the working directory the spawn set up
before `preexec_fn` still names the underlying writable mount, so
only a re-entry makes a relative write meet the read-only bind —
and a failure of that re-entry SHALL be reported on the read-only
guarantee as not enforced, never silently. The run's probe SHALL
perform the same remount and re-entry, so its answer matches what
a stage gets. A `post-gate` stage's candidate is not bound. A
`writes` the manifest declares beyond the candidate has no
enforcement in this mechanism — the naming requirement reports it
rather than imply a sandbox that does not exist. A mount this
platform or environment cannot make SHALL NOT stop the stage: the
stage still runs, and what could not be enforced is named under
the naming requirement.

#### Scenario: a pre-gate stage's candidate directory is bound read-only over itself
- **WHEN** a `pre-gate` stage runs where the platform and
  environment allow the mount
- **THEN** in its child the candidate directory is bound over itself
  and remounted `MS_BIND | MS_REMOUNT | MS_RDONLY`, in a mount
  namespace with private propagation — and nothing outside the
  candidate is made read-only

#### Scenario: the read-only remount keeps the flags the candidate's mount locks
- **WHEN** a `pre-gate` stage runs on a candidate whose mount's
  `f_flag` reports `nosuid`, `nodev` and `relatime` — the `/tmp`
  case
- **THEN** the remount carries `MS_BIND | MS_REMOUNT | MS_RDONLY`
  with `MS_NOSUID`, `MS_NODEV` and `MS_RELATIME` added — the bind
  becomes read-only rather than refused `EPERM`

#### Scenario: each locked flag statvfs reports is mapped to its mount flag
- **WHEN** `f_flag` holds each of `ST_NOSUID`, `ST_NODEV`,
  `ST_NOEXEC`, `ST_NOATIME`, `ST_NODIRATIME` and `ST_RELATIME`,
  alone or together
- **THEN** the mapping answers the matching `MS_NOSUID`,
  `MS_NODEV`, `MS_NOEXEC`, `MS_NOATIME`, `MS_NODIRATIME` and
  `MS_RELATIME` — and nothing for a bit the mount lock does not
  cover

#### Scenario: the child re-enters the candidate after the read-only remount
- **WHEN** the bind and the remount have completed in the stage's
  child
- **THEN** the child changes its working directory to the candidate
  again — after the remount and before the capability drop and
  `execve` — so a relative write meets the read-only mount

#### Scenario: a re-entry that fails is named on the read-only guarantee
- **WHEN** the child's `os.chdir` to the candidate refuses
- **THEN** the failure is reported on the `read-only candidate`
  guarantee as not enforced — never silently — and the stage still
  runs

#### Scenario: the probe performs the same remount and re-entry the stage gets
- **WHEN** the run's probe checks the read-only guarantee
- **THEN** its throwaway child runs the same sequence — the
  statvfs-mapped remount and the re-entry — so its answer matches
  what a stage gets

#### Scenario: a stage cannot write the candidate by a relative or an absolute path
- **WHEN** a stage runs on a platform where the read-only floor is
  enforceable
- **THEN** its write into the candidate through a relative path is
  refused and its write through an absolute path is refused alike

#### Scenario: a mount the platform refuses is named and the stage still runs
- **WHEN** the run's probe reports the platform or environment
  cannot make the read-only bind
- **THEN** the stage still runs and its note names `not enforced:
  read-only candidate (<reason>)` with the probe's reason

#### Scenario: a post-gate stage's candidate is not bound read-only
- **WHEN** a `post-gate` stage runs
- **THEN** no read-only bind is attempted for it — the floor is the
  pre-gate's alone

#### Scenario: a declared writes beyond the candidate is reported as not enforced
- **WHEN** a stage runs whose manifest declares `isolation.writes`
- **THEN** its note names `not enforced: writes beyond the
  candidate (<reason>)` — the core has no filesystem sandbox beyond
  the candidate and says so rather than imply one

#### Scenario: an isolated stage cannot reach the network or write the candidate
- **WHEN** a stage runs on a platform where the probe finds the
  guarantees enforceable
- **THEN** the stage's `CapEff`, `CapPrm` and `CapBnd` are all zero,
  an attempt to remount the candidate read-write and an attempt to
  unmount it both fail, its attempt to open a network connection
  fails and its attempt to write into the candidate directory fails —
  and where a guarantee is not enforceable there, the note names it
