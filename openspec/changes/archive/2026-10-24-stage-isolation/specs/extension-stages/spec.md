# extension-stages Specification (delta)

## MODIFIED Requirements

### Requirement: the command runs as an argv process under the core's interpreter

Each stage's `command` SHALL run as the argv list `[<the Python
interpreter the core runs under>, <the path under bin/>]` — never
through a shell and never through `PATH` lookup — with its working
directory the candidate snapshot and an environment of a minimal
`PATH` of `/usr/bin:/bin` that the core always sets, each
`isolation.env` name the caller holds — except at `pre-gate`, where
a provider secret is withheld even when `isolation.env` names it: a
name on the core's fixed provider list or ending `_API_KEY`,
`_TOKEN`, `_SECRET` or `_PASSWORD` SHALL NOT be passed through, and
the run's output SHALL note the withheld declared names once — and
the five protocol variables `AGENTMARSHAL_PHASE`,
`AGENTMARSHAL_TASK`, `AGENTMARSHAL_COMMIT`, `AGENTMARSHAL_BASE` and
`AGENTMARSHAL_SNAPSHOT` written last so a declared name colliding
with one cannot override the run's own values. A `PATH` named in
`isolation.env` SHALL NOT be passed through — the core's minimal
`PATH` stands — and the run's output SHALL say so. A `command`
path that does not exist or is a symbolic link SHALL be `not run`
naming why; a process that cannot be started SHALL be `not run`
naming why. Exit status 0 SHALL decide `checked`; any other exit
status SHALL decide `failed`.

#### Scenario: the command runs under the core's interpreter, never through a shell
- **WHEN** a stage's `command` is a file with no execute bit and no
  shebang the system would honour
- **THEN** it runs — the interpreter is the core's own — and nothing
  the shell would have expanded is expanded

#### Scenario: the environment carries the protocol variables and a minimal PATH
- **WHEN** a stage runs
- **THEN** its environment carries `AGENTMARSHAL_PHASE`,
  `AGENTMARSHAL_TASK`, `AGENTMARSHAL_COMMIT`, `AGENTMARSHAL_BASE` and
  `AGENTMARSHAL_SNAPSHOT` with the run's own values and a minimal
  `PATH`, and no other variable of the caller's

#### Scenario: only the environment variables the manifest names are passed
- **WHEN** a manifest's `isolation.env` names one variable the caller
  holds and the caller holds another the manifest does not name
- **THEN** the named variable reaches the stage and the unnamed one
  does not

#### Scenario: a provider secret named in isolation.env is withheld at pre-gate
- **WHEN** a manifest's `isolation.env` names a provider secret —
  `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GITHUB_TOKEN`, `GH_TOKEN`
  or `GITLAB_TOKEN` — and the caller holds it
- **THEN** at `--phase pre-gate` the stage does not receive it, while
  a declared non-secret name still does

#### Scenario: a name ending in a provider-secret suffix is withheld at pre-gate
- **WHEN** a manifest's `isolation.env` names a variable ending
  `_API_KEY`, `_TOKEN`, `_SECRET` or `_PASSWORD` and the caller
  holds it
- **THEN** at `--phase pre-gate` the stage does not receive it

#### Scenario: a declared provider secret reaches a post-gate stage
- **WHEN** a manifest's `isolation.env` names a provider secret and
  the caller holds it
- **THEN** at `--phase post-gate` the stage receives the caller's
  value — the withholding floor is the pre-gate's alone

#### Scenario: the withheld provider-secret names are noted once
- **WHEN** planned manifests name provider secrets in `isolation.env`
- **THEN** the run's output notes once — however many extensions
  declare them — which declared names were withheld at pre-gate

#### Scenario: a PATH named in isolation.env is not passed through
- **WHEN** a manifest's `isolation.env` names `PATH` and the caller
  holds it
- **THEN** the stage sees the core's minimal `PATH` — not the
  caller's — and the run's output says so

#### Scenario: a protocol variable cannot be overridden by a declared name
- **WHEN** a manifest's `isolation.env` names an `AGENTMARSHAL_*`
  variable and the caller holds it with a foreign value
- **THEN** the stage sees the run's own value

#### Scenario: a missing command is not run naming why
- **WHEN** a stage's `command` names a path that does not exist in the
  materialized directory
- **THEN** the stage is `not run` naming why

#### Scenario: a symlinked command is not run
- **WHEN** a stage's `command` path is a symbolic link in the
  materialized directory
- **THEN** the stage is `not run` as a symbolic link

#### Scenario: exit status zero checks and any other fails
- **WHEN** one stage exits 0 and another exits nonzero
- **THEN** the first is `checked` and the second `failed` naming the
  exit status

## ADDED Requirements

### Requirement: a stage with no declared network runs in a new user and network namespace

On Linux, a stage whose manifest does not declare `network = true`
SHALL run with no network the stage can reach: the stage's own child
SHALL enter a new user and network namespace —
`os.unshare(CLONE_NEWUSER | CLONE_NEWNET)` after `fork` and before
`execve`, `deny` written to `/proc/self/setgroups` and a one-line
identity mapping of the caller's uid and gid written to
`/proc/self/uid_map` and `/proc/self/gid_map` — applied by the core
itself, never a wrapper process, a shell or a tool looked up on
`PATH`. A stage whose manifest declares `network = true` SHALL run
as before. Namespaces this platform or environment cannot provide
SHALL NOT stop the stage: the stage still runs, and what could not
be enforced is named under the naming requirement.

#### Scenario: a stage whose manifest declares no network runs in a new user and network namespace
- **WHEN** a stage runs whose manifest declares no `[isolation]`
  `network = true`
- **THEN** the stage's child enters a new user and network namespace
  by the core's own `preexec`-style setup before exec — never a
  wrapper or a shell

#### Scenario: a stage declaring network = true runs without the network namespace
- **WHEN** a stage runs whose manifest declares `network = true`
- **THEN** no network namespace is attempted for it and no
  `not enforced: network` note appears

#### Scenario: a network namespace the platform refuses is named and the stage still runs
- **WHEN** the run's probe reports the platform or environment
  cannot provide the user and network namespaces
- **THEN** the stage still runs and its note names `not enforced:
  network (<reason>)` with the probe's reason

### Requirement: a pre-gate stage's candidate is bound read-only over itself

At `pre-gate`, the stage's candidate working directory SHALL be
read-only to the stage: in the same child, in a new mount
namespace, `mount(NULL, "/", NULL, MS_REC | MS_PRIVATE)` makes
propagation private, a bind mounts the candidate directory onto
itself and a `MS_BIND | MS_REMOUNT | MS_RDONLY` remount turns the
bind read-only — the mounts made by libc's `mount` through the
core, and nothing outside the candidate directory made read-only. A
`post-gate` stage's candidate is not bound. A `writes` the manifest
declares beyond the candidate has no enforcement in this mechanism
— the naming requirement reports it rather than imply a sandbox
that does not exist. A mount this platform or environment cannot
make SHALL NOT stop the stage: the stage still runs, and what could
not be enforced is named under the naming requirement.

#### Scenario: a pre-gate stage's candidate directory is bound read-only over itself
- **WHEN** a `pre-gate` stage runs where the platform and
  environment allow the mount
- **THEN** in its child the candidate directory is bound over itself
  and remounted `MS_BIND | MS_REMOUNT | MS_RDONLY`, in a mount
  namespace with private propagation — and nothing outside the
  candidate is made read-only

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
- **THEN** the stage's attempt to open a network connection fails
  and its attempt to write into the candidate directory fails —
  and where a guarantee is not enforceable there, the note names it

### Requirement: a guarantee the core cannot enforce is named, never silently weakened

The core SHALL answer once per run — a probe in a throwaway child
running the real sequence and dying with it, its verdict cached —
which guarantees this platform and environment allow, asked at the
first stage that runs so the answer precedes the stage rather than
following it. Each guarantee a stage is owed that the probe or the
stage's own setup could not enforce SHALL be named on one note
line for the stage, each with its reason — `not enforced:
<guarantee> (<reason>)`, as `network`, `read-only candidate` and
`writes beyond the candidate` are named — and the stage SHALL still
run; a guarantee enforced SHALL NOT be mentioned, so a platform
enforcing everything shows unchanged output. A setup step that
fails in the stage's own child after the probe allowed it SHALL be
named the same way: the child reports the failure on its stderr
ahead of its exec'd output, and the run strips the report out of
the stream it reframes — never a silent weakening. A stage that
does not run at all SHALL carry no isolation note.

#### Scenario: each guarantee not enforced is named on one note line for the stage
- **WHEN** a stage is owed guarantees the platform cannot enforce
- **THEN** one `stage run: note: <name>: not enforced: <guarantee>
  (<reason>); …` line names each with its reason beside the stage's
  result line

#### Scenario: an enforced guarantee is not mentioned
- **WHEN** every guarantee a stage is owed is enforced
- **THEN** no `not enforced` note appears — output is unchanged

#### Scenario: a setup step that fails in the stage's own child is named
- **WHEN** the probe allowed a guarantee but a setup step still
  fails in the stage's child
- **THEN** the failure is reported out of the child's stderr ahead
  of the stage's output, stripped from the framed stream, and the
  guarantee is named `not enforced` the same way

#### Scenario: a platform without namespaces names each guarantee it cannot enforce
- **WHEN** the run's probe reports a platform with no namespace
  support — a non-Linux system or a Python without `os.unshare` —
- **THEN** every guarantee a stage is owed is named not enforced
  with the probe's reason, and the stage still runs

#### Scenario: the probe runs once per run
- **WHEN** several stages run in one invocation
- **THEN** the probe's throwaway child runs once and every stage
  shares its verdict

#### Scenario: a stage that does not run carries no isolation note
- **WHEN** a stage's result is `not run` or `switched off`
- **THEN** no `not enforced` note appears for it — a stage that
  never started was owed no guarantees
