# extension-stages Specification (delta)

## MODIFIED Requirements

### Requirement: the command runs as an argv process under the core's interpreter

Each stage's `command` SHALL run as the argv list `[<the Python
interpreter the core runs under>, <the path under bin/>]` — never
through a shell and never through `PATH` lookup — with its working
directory the candidate snapshot and an environment of a minimal
`PATH` of `/usr/bin:/bin` that the core always sets, each
`isolation.env` name the caller holds, and the five protocol
variables `AGENTMARSHAL_PHASE`, `AGENTMARSHAL_TASK`,
`AGENTMARSHAL_COMMIT`, `AGENTMARSHAL_BASE` and `AGENTMARSHAL_SNAPSHOT`
written last so a declared name colliding with one cannot override the
run's own values. A `PATH` named in `isolation.env` SHALL NOT be
passed through — the core's minimal `PATH` stands — and the run's
output SHALL say so. A `command` path that does not exist or is a
symbolic link SHALL be `not run` naming why; a process that cannot be
started SHALL be `not run` naming why. Exit status 0 SHALL decide
`checked`; any other exit status SHALL decide `failed`.

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
