# extension-stages Specification

## Purpose
The declared stages of shared extensions, invoked at the two lifecycle
points an extension may act — ADR-0013 section A, decisions 1, 2, 4, 5
and 7. `agentmarshal stage run --phase <pre-gate|post-gate> --task <id>
--commit <rev> --base <ref>` is a separate step beside the gate: it
reads each shared extension's manifest from the base commit — never
the candidate's tree and never the working tree — materializes the
extension's directory from that tree, and runs every `[[stage]]` whose
phase the invocation selects under the core's interpreter as an argv
process, in a snapshot of the candidate commit, bounded by the declared
`timeout_seconds` capped at the core's 600-second limit. On a
workstation a stage runs only under a local grant matching the
base-materialized contents (decision 14); in CI none is needed. Every
stage gets exactly one result line — `checked`, `failed (exit <n>)`,
`did not finish (timeout)` or `not run (<reason>)` — and its output a
frame that cannot read as one; each result appends an
`extension-event` to the process log (ADR-0022 section 7). A
`pre-gate-stop` stage that failed, did not finish or did not run pauses
the process before the gate — the command exits 3 — while a
`pre-gate-warn` stage's failure is only a loud warning and a
`post-gate` stage's only a notification. Extensions cannot alter the
gate's decisions: the gate reads none of this, the command writes no
journal, and network isolation, write isolation and pause records are
later work, not this capability.

## Requirements

### Requirement: `stage run` invokes the declared stages of the base's shared extensions

`agentmarshal stage run --phase <pre-gate|post-gate> --task <id>
--commit <rev> --base <ref>` SHALL resolve `--commit` and `--base` to
commits, compute their merge base, and read each shared extension's
manifest at that merge base — the names enumerated from the tree's
`.agentmarshal/extensions/` entries — with the gate's own base-tree
reader, so the tree rules for a manifest in both forms, a link entry
and a schema-1 directory form are the gate's rather than restated. A
link at `.agentmarshal`, at `extensions/` or at an extension's `<name>`
entry SHALL be refused as a link; an `extensions/` that is missing or
not a tree SHALL mean no directory-form extensions. A `--phase
pre-gate` invocation SHALL run each `[[stage]]` whose phase is
`pre-gate-warn` or `pre-gate-stop`; a `--phase post-gate` invocation
SHALL run each whose phase is `post-gate`. Extensions SHALL run in the
sorted order of their names, each extension's matching stages in the
order its manifest declares. A manifest the base-tree reader refuses
SHALL fail the command naming the extension and its tree source. A
file-form extension SHALL have no stage to run — it declares no
directory. A sidecar SHALL refuse: a stage's base is a property of the
embedded placement. An invalid task identifier SHALL refuse before any
manifest is read.

#### Scenario: pre-gate invokes the pre-gate-warn and pre-gate-stop stages
- **WHEN** `stage run --phase pre-gate` runs against an extension whose
  manifest declares a `pre-gate-warn` stage, a `pre-gate-stop` stage
  and a `post-gate` stage
- **THEN** the `pre-gate-warn` and `pre-gate-stop` stages run and the
  `post-gate` stage does not

#### Scenario: post-gate invokes the post-gate stages
- **WHEN** `stage run --phase post-gate` runs against an extension
  declaring a `post-gate` stage and a `pre-gate-stop` stage
- **THEN** the `post-gate` stage runs and the `pre-gate-stop` stage
  does not

#### Scenario: stages run in extension-name order and manifest order within
- **WHEN** two extensions each declare stages and one declares two of
  the same phase
- **THEN** the extensions run in the sorted order of their names and
  each extension's stages in its manifest's declared order

#### Scenario: a manifest the base cannot parse fails the run naming the extension
- **WHEN** an extension's manifest at the base tree is unreadable or
  invalid
- **THEN** `stage run` fails naming the extension and its tree source,
  and no stage is planned

#### Scenario: a file-form extension has no stage to run
- **WHEN** `stage run` runs where `.agentmarshal/extensions/` holds
  only `<name>.toml` entries
- **THEN** no stage is planned and the command says no shared extension
  declares a matching stage

#### Scenario: a sidecar runs no stages
- **WHEN** `stage run` runs where the journal placement is a sidecar
- **THEN** it refuses saying a sidecar runs no stages and nothing runs

#### Scenario: an invalid task identifier refuses before any stage is planned
- **WHEN** `stage run` is given a `--task` value the record family
  would refuse
- **THEN** it refuses naming the identifier and no stage is planned

### Requirement: the extension's code is the base's and the working directory the candidate's

Each stage's extension directory SHALL be materialized from the merge
base's tree into a fresh temporary directory — each blob under
`.agentmarshal/extensions/<name>/` written byte for byte from `git
show`, a symbolic-link entry recreated as a link, a non-blob entry
refused as not materializable — and the stage's working directory
SHALL be a fresh temporary snapshot of the candidate commit produced
by `git archive`. The materialization and the snapshot SHALL be each
stage's own: no stage runs against a copy an earlier stage produced.
A materialized directory holding a symbolic link anywhere SHALL make
each of the extension's stages `not run (symlink in extension
directory: <path>)` — the refusal the grant hash gives on a
workstation, applied in CI too, where a linked intermediate directory
would otherwise put the command outside the approved copy. Neither
SHALL read the working tree, and the temporary directories SHALL be
removed when the command returns. A directory that cannot be
materialized SHALL make each of the extension's stages `not run`
naming why; a snapshot that cannot be materialized SHALL make that
stage `not run` naming why.

#### Scenario: the base commit's code runs, not the candidate's or the working tree's
- **WHEN** the candidate commit or the working tree carries a changed
  `bin/` script or a changed manifest
- **THEN** the stage that runs is the base commit's — the changed code
  and manifest play no part

#### Scenario: the working directory is a snapshot of the candidate commit
- **WHEN** a stage runs
- **THEN** its working directory holds the candidate commit's files and
  not the working tree's uncommitted or base-only contents

#### Scenario: an earlier stage cannot rewrite a later stage's command
- **WHEN** one extension declares two matching stages and the first
  stage rewrites the second stage's command inside its own
  materialized copy of the extension directory
- **THEN** the second stage still runs the base commit's command —
  each stage's materialization is its own

#### Scenario: a symbolic link inside the extension's directory is recreated as a link
- **WHEN** the base's extension directory contains a symbolic-link
  entry
- **THEN** the materialized directory holds a link at that path, and
  each of the extension's stages is `not run (symlink in extension
  directory: <path>)` — rather than a copy of whatever the working
  tree's link resolves to

#### Scenario: a gitlink inside the extension's directory is not run
- **WHEN** the base's extension directory contains a submodule entry
- **THEN** the extension's stages are `not run` naming why

#### Scenario: the temporary directories are gone when the command returns
- **WHEN** `stage run` finishes — checked, failed or paused
- **THEN** no materialized directory or snapshot remains

### Requirement: the command runs as an argv process under the core's interpreter

Each stage's `command` SHALL run as the argv list `[<the Python
interpreter the core runs under>, <the path under bin/>]` — never
through a shell and never through `PATH` lookup — with its working
directory the candidate snapshot and an environment of a minimal
`PATH`, each `isolation.env` name the caller holds, and the five
protocol variables `AGENTMARSHAL_PHASE`, `AGENTMARSHAL_TASK`,
`AGENTMARSHAL_COMMIT`, `AGENTMARSHAL_BASE` and `AGENTMARSHAL_SNAPSHOT`
written last so a declared name colliding with one cannot override the
run's own values. A `command` path that does not exist or is a
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

### Requirement: a stage is bounded by its declared timeout capped at the core's limit

Each stage SHALL be bounded by the manifest's declared
`timeout_seconds` capped at the core's limit — a module-level constant
of 600 seconds; a manifest declaring no isolation gets the core's
limit. On a breach the child's whole process group SHALL be killed and
the result SHALL be `did not finish (timeout)`.

#### Scenario: a stage over its declared timeout is killed and did not finish
- **WHEN** a stage's declared `timeout_seconds` elapses before the
  process exits
- **THEN** the process group is killed and the result is
  `did not finish (timeout)`

#### Scenario: the core's limit caps a longer declared timeout
- **WHEN** a manifest declares a `timeout_seconds` above the core's
  limit
- **THEN** the stage is killed at the core's limit, not the declared
  one

### Requirement: on a workstation a stage runs only under a matching grant

On a workstation — `CI` not equal to `true` — each stage's extension
SHALL hold a grant in the clone's `trust.toml` whose per-file hashes
match a fresh hash of the base-materialized directory: no grant SHALL
be `not run (not granted)` and a difference SHALL be `not run (changed
after approval: <file>)` naming the first differing file, recomputed
per the trust file's own walk — a symbolic link or a non-regular file
inside the materialized directory SHALL be the `not run` reason. In CI
— `CI` equal to `true` — no grant is needed. A `trust.toml` the
grants reader refuses SHALL fail the command naming the file.

#### Scenario: no grant on a workstation is not run
- **WHEN** `stage run` runs on a workstation where `trust.toml` holds
  no grant for the extension
- **THEN** each of its stages is `not run (not granted)`

#### Scenario: a grant matching the base contents runs the stage
- **WHEN** the recorded grant's per-file hashes match the
  base-materialized directory
- **THEN** the stage runs

#### Scenario: a grant for different contents is not run naming the changed file
- **WHEN** the recorded grant's hashes differ from the
  base-materialized directory
- **THEN** each of the extension's stages is `not run (changed after
  approval: <file>)` naming the first differing file

#### Scenario: in CI no grant is needed
- **WHEN** `stage run` runs with `CI=true` and no grant recorded
- **THEN** the stage runs without consulting `trust.toml`

#### Scenario: a malformed trust.toml fails the command naming it
- **WHEN** `stage run` runs on a workstation where `trust.toml` is
  malformed
- **THEN** the command fails naming the file and no stage is planned

### Requirement: every stage gets exactly one result line and its output a frame

Each stage SHALL print exactly one result line on stdout: `<name>:
checked`, `<name>: failed (exit <n>)`, `<name>: did not finish
(timeout)` or `<name>: not run (<reason>)`. The extension's own
captured output SHALL be reprinted one line each as `<name> | <line>`
with every forgeable character escaped, so no output line reads as a
result line or as another extension's.

#### Scenario: a checked stage prints its checked line
- **WHEN** a stage's process exits 0
- **THEN** the result line is `<name>: checked`

#### Scenario: a failed stage prints failed (exit <n>)
- **WHEN** a stage's process exits nonzero
- **THEN** the result line is `<name>: failed (exit <n>)` naming the
  status

#### Scenario: a timed-out stage prints did not finish (timeout)
- **WHEN** a stage is killed on its time limit
- **THEN** the result line is `<name>: did not finish (timeout)`

#### Scenario: a stage that may not run prints not run (<reason>)
- **WHEN** a stage's grant, materialization or command refuses it
- **THEN** the result line is `<name>: not run (<reason>)` naming why

#### Scenario: the extension's output is framed so it cannot read as a result line
- **WHEN** a stage prints a line shaped like a result line or carrying
  a forgeable character
- **THEN** it appears as `<name> | <line>` — escaped — and never as an
  unframed line

#### Scenario: every stage gets exactly one result line
- **WHEN** several extensions' stages run
- **THEN** each stage prints exactly one result line — never none,
  never two

### Requirement: each result is appended to the process log as an extension-event

Each stage's result SHALL append one `extension-event` to the process
log (ADR-0022 section 7) carrying the extension's name, `scope`
`shared`, the stage's own `phase`, the `decision` — `checked`,
`failed`, `did-not-finish` or `not-run` — the `reason`, the resolved
`commit` and the task, and a `post-gate` stage's event SHALL also
carry `result`. A process log that cannot be opened or written SHALL
be a warning on stderr naming it — the result line and the exit status
SHALL NOT change for it.

#### Scenario: each stage's result appends one extension-event
- **WHEN** stages run
- **THEN** each appends one `extension-event` carrying the extension,
  `scope` `shared`, the stage's own phase, the decision, the reason,
  the resolved commit and the task

#### Scenario: a post-gate stage's event carries the result field
- **WHEN** a `post-gate` stage's result is appended
- **THEN** the event carries `result` as well

#### Scenario: a lost process log is a warning, not a changed verdict
- **WHEN** the process log cannot be opened or written
- **THEN** a warning names it on stderr and the result line and the
  exit status are unchanged

### Requirement: a pre-gate-stop stage that did not check pauses the process before the gate

The command SHALL print that the process is paused before the gate —
naming the stage — and SHALL exit 3 when any `pre-gate-stop` stage's
decision is not `checked`: failed, did not finish or did not run. A
`pre-gate-warn` stage whose decision is not `checked` SHALL print a
warning naming it and SHALL NOT change the exit; a `post-gate` stage
SHALL never pause. Otherwise the command SHALL exit 0.

#### Scenario: a failed pre-gate-stop stage pauses the process before the gate
- **WHEN** a `pre-gate-stop` stage's decision is `failed`
- **THEN** the command prints that the process is paused before the
  gate naming the stage and exits 3

#### Scenario: a pre-gate-stop stage that did not run pauses the process
- **WHEN** a `pre-gate-stop` stage's decision is `did-not-finish` or
  `not-run`
- **THEN** the command pauses and exits 3 the same way

#### Scenario: a failed pre-gate-warn stage warns and the exit is 0
- **WHEN** a `pre-gate-warn` stage's decision is `failed`
- **THEN** the command prints a warning naming the stage and exits 0

#### Scenario: a checked pre-gate-stop stage does not pause
- **WHEN** every `pre-gate-stop` stage's decision is `checked`
- **THEN** nothing is paused and the command exits 0

#### Scenario: a post-gate stage's outcome never pauses
- **WHEN** a `post-gate` stage fails or does not run
- **THEN** the command exits 0 and prints no pause

### Requirement: the command is registered like `step` and writes no journal

The `stage` group SHALL be registered from `stages.py`'s
`register`/`run` pair on the command-line parser, the way the `step`
group is, with a `run` subcommand. The command SHALL write nothing to
the journal and SHALL change neither the gate nor any other command.

#### Scenario: the stage group takes run --phase --task --commit --base
- **WHEN** the command-line parser is built
- **THEN** `agentmarshal stage run --phase <phase> --task <id>
  --commit <rev> --base <ref>` parses, and an unknown `stage`
  subcommand is refused

#### Scenario: the journal is untouched
- **WHEN** `stage run` finishes — checked, failed or paused
- **THEN** `.agentmarshal/journal/` is unchanged
