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
SHALL run each whose phase is `post-gate`. One exception precedes the
manifest read for `--phase pre-gate`: on a candidate the gate's own
operational-lane predicate qualifies — decided by the same function
the gate uses, imported rather than copied — the invocation SHALL
print one line saying pre-gate stages do not run on an operational
change and SHALL run no stage, reading no extension manifest and
consulting no switch to decide one — no extension event, no pause —
returning success (ADR-0013 decision 17: otherwise a broken extension
blocks its own switching off). Extensions SHALL run in the
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

#### Scenario: pre-gate stages do not run on an operational change
- **WHEN** `stage run --phase pre-gate` runs on a candidate the gate's
  operational lane admits — a switches-only diff under a contract
  scoping exactly `.agentmarshal/switches.toml`
- **THEN** it prints one line saying pre-gate stages do not run on an
  operational change, reads no extension manifest, runs no stage and
  exits 0

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
decision is not `checked`: failed, did not finish or did not run —
unless the stage's pause is accepted under the accepted-pause
requirement, in which case the pause stands down as that requirement
states. A `pre-gate-warn` stage whose decision is not `checked` SHALL
print a warning naming it and SHALL NOT change the exit; a `post-gate`
stage SHALL never pause. Otherwise the command SHALL exit 0.

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

### Requirement: `.agentmarshal/switches.toml` is parsed by one function

The shared switches file SHALL carry `format = 1` and a `[switches]`
table holding, per extension name, a table of `state` — `"on"` or
`"off"` — `task` — the operational CR that set the switch, matching
`CR-<n>` — and `reason`. `reason` SHALL be required when `state` is
`"off"` and SHALL be refused when `state` is `"on"`; present, it is at
most 1000 characters and passes the forgeable-text rule. Keys an entry
carries beyond those SHALL pass unread. One function SHALL parse the
file's bytes against the shared extension names the caller knows: text
that is not UTF-8 TOML, a missing `format`, an unknown `format`, a
`switches` that is not a table, an entry that is not a table, an entry
naming no shared extension, a `state` outside `"on"` and `"off"`, a
`task` that is not a `CR-<n>` identifier, or a `reason` outside its
rule SHALL each be refused naming the file and, where one exists, the
entry. The refusal SHALL carry the entry names the file declares where
they could be enumerated. A missing file SHALL mean every extension is
on.

#### Scenario: an off switch parses with its task and reason
- **WHEN** `switches.toml` holds `format = 1` and an entry
  `[switches.openspec]` with `state = "off"`, `task = "CR-214"` and a
  `reason`
- **THEN** the parse returns the extension's switch — `off`, `CR-214`
  and the reason

#### Scenario: a missing switches file means every extension is on
- **WHEN** the file does not exist
- **THEN** the read returns an empty set — every extension is on

#### Scenario: a file that is not TOML is refused naming it
- **WHEN** the file's text is not UTF-8 TOML
- **THEN** the parse is refused naming the file

#### Scenario: an unknown or missing format is refused naming the file
- **WHEN** the file declares no `format` or a `format` other than 1
- **THEN** the parse is refused naming the file

#### Scenario: an entry naming no shared extension is refused naming the file and the entry
- **WHEN** a `switches` entry names an extension the caller does not
  know
- **THEN** the parse is refused naming the file and the entry

#### Scenario: a switch entry outside its shape is refused naming the file and the entry
- **WHEN** an entry is not a table, has a `state` outside `"on"` and
  `"off"`, a `task` that is not `CR-<n>`, an `off` with no `reason`, an
  `on` carrying a `reason`, or a `reason` over 1000 characters or
  carrying a forgeable character
- **THEN** the parse is refused naming the file and the entry

### Requirement: `stage run` reads the switches from the base and reports a switched-off extension

`stage run` SHALL read `.agentmarshal/switches.toml` from the merge
base's tree — never the candidate's and never the working tree's —
parsed against every shared extension name the base's
`.agentmarshal/extensions/` enumerates, both forms. An entry at the
file's path that is not a file SHALL be the file's own malformation.
Each stage of a switched-off extension SHALL print `<name>: switched
off (<task>, <reason>)` as its one result line, the values escaped for
display, and SHALL NOT run: the extension is neither materialized nor
grant-checked for that stage. Its `extension-event` SHALL carry the
decision `switched-off` and a reason of `<task>, <reason>`. A
switched-off stage SHALL neither pause a `pre-gate-stop` nor warn a
`pre-gate-warn`. A switches file the parse refuses SHALL be reported on
one line on stderr naming the file and, where the parse reached one,
the entry; no stage of an extension the file names SHALL run — each
SHALL be `not run (shared switches file unreadable)` — and where the
file's entries cannot be enumerated at all, every stage SHALL be. On a
`--phase pre-gate` invocation the operational lane excepts, no stage is
planned at all — the exception the invocation requirement states — so
a switched-off extension's stage carries no `switched off` line there;
the read of the merge base's file this requirement governs is still
made, by the lane's own predicate, and never of the candidate's or the
working tree's file.

#### Scenario: a switched-off extension prints switched off (task, reason) and does not run
- **WHEN** the base's switches file switches an extension off
- **THEN** each of its matching stages prints `<name>: switched off
  (<task>, <reason>)` and the extension does not run

#### Scenario: the switches are read from the base commit, never the candidate or the working tree
- **WHEN** the candidate's tree or the working tree carries a different
  switches file — one switching the extension on, or off
- **THEN** the base's file decides: a base switch-off still reports
  `switched off`, a base all-on still runs

#### Scenario: a switched-off pre-gate-stop stage does not pause
- **WHEN** a `pre-gate-stop` extension is switched off
- **THEN** the command does not pause and exits 0

#### Scenario: every stage of a switched-off extension gets the switched-off line
- **WHEN** a switched-off extension declares two matching stages
- **THEN** each prints `switched off (<task>, <reason>)` — two result
  lines, no run

#### Scenario: a switched-off stage's event carries the switched-off decision, the task and the reason
- **WHEN** a switched-off stage's result is appended to the process log
- **THEN** the event carries decision `switched-off` and reason
  `<task>, <reason>`

#### Scenario: an extension switched on or with no entry runs
- **WHEN** the file switches one extension `on` and names another not
  at all
- **THEN** both run as before

#### Scenario: a malformed switches file is reported on one line and no stage of an extension it names runs
- **WHEN** the base's switches file parses but holds an entry outside
  its shape
- **THEN** the refusal is printed on one stderr line naming the file
  and the entry, every named extension's stages are `not run`, and an
  extension the file does not name still runs

#### Scenario: a switches file that cannot be read leaves every stage not run
- **WHEN** the base's switches file is not TOML at all
- **THEN** the refusal is printed on one stderr line and every stage is
  `not run (shared switches file unreadable)`

#### Scenario: an operational change reports no switched-off stage
- **WHEN** `stage run --phase pre-gate` runs on a candidate the
  operational lane admits while the base's file already switches an
  extension off
- **THEN** the command's one line is the operational skip — no stage of
  the switched-off extension prints `switched off` — and it exits 0

### Requirement: `doctor` shows each switched-off shared extension

`doctor` SHALL read `.agentmarshal/switches.toml` from the working
tree, parsed against the shared extension names the working tree
enumerates, and SHALL show each switched-off shared extension's line
carrying `switched off since <task> (<reason>)` — for the file form
and the directory form alike, and on the line of an extension whose
manifest cannot be read — every value from the file escaped on
display. A project without the file SHALL show nothing new: every
extension is on. A file the parse refuses SHALL be named on one
`switches: unavailable (<reason>)` line, never a check failure.

#### Scenario: doctor shows a switched-off extension with its task and reason
- **WHEN** the working tree's switches file switches an extension off
- **THEN** its line carries `switched off since <task> (<reason>)`

#### Scenario: a project without switches.toml shows nothing new
- **WHEN** the project has no `switches.toml`
- **THEN** the extensions section reads as before — every extension is
  on

#### Scenario: an extension switched on or with no entry shows no switch
- **WHEN** the file switches one extension `on` and names another not
  at all
- **THEN** neither line mentions the switch

#### Scenario: a file-form extension switched off is shown the same way
- **WHEN** the file switches off a `<name>.toml` extension
- **THEN** its line carries `switched off since <task> (<reason>)`

#### Scenario: a malformed switches file is named on one line and fails nothing
- **WHEN** the working tree's switches file is refused by the parse
- **THEN** one `switches: unavailable (<reason>)` line names it, and no
  check fails for it

#### Scenario: a value that could forge a line is escaped on display
- **WHEN** a switches entry's name carries a forgeable character and
  the refusal quotes it
- **THEN** the displayed line carries the escape, not the character

### Requirement: `extension switch off` opens an operational task and writes the switch

`agentmarshal extension switch off <name> --reason <text>` SHALL open a
task through the journal's `open_task` — a contract whose title names
the extension, whose scope is exactly `[".agentmarshal/switches.toml"]`
and whose acceptance says the extension is switched off with the
reason — and SHALL write into the working tree's
`.agentmarshal/switches.toml` the entry `state = "off"`,
`task = <the opened task's id>` and `reason = <text>`, creating the
file with `format = 1` and a `[switches]` table when absent. The
command SHALL print the opened contract's and record's paths as `open`
does, then the switches file's path, and SHALL commit nothing.

#### Scenario: the opened contract names the extension, scopes the switches file and accepts the switch-off
- **WHEN** `extension switch off openspec --reason "…"` runs where
  `openspec` is a shared extension the working tree declares
- **THEN** the opened contract's title names `openspec`, its scope is
  exactly `[".agentmarshal/switches.toml"]` and its acceptance says
  `openspec` is switched off with the reason

#### Scenario: the switches entry is written for the opened task
- **WHEN** the command opens the task `CR-001`
- **THEN** the file's `[switches.openspec]` entry carries
  `state = "off"`, `task = "CR-001"` and the given `reason`

#### Scenario: a missing switches file is created with format and the switches table
- **WHEN** `.agentmarshal/switches.toml` does not exist
- **THEN** the command creates it carrying `format = 1`, a `[switches]`
  table and the off entry

#### Scenario: the paths are printed and nothing is committed
- **WHEN** the command succeeds
- **THEN** stdout carries the opened contract's path, the opened
  record's path and the switches file's path, and HEAD does not move

### Requirement: name, reason and the existing file are checked before the task is opened

The name SHALL be a shared extension the working tree declares — a
name `doctor` and `stage run` enumerate under
`.agentmarshal/extensions/`: a `<name>.toml` entry, a `<name>/`
directory, or a link entry kept under the name it carries — whether
or not the manifest under it can be read, since a broken extension
must stay switchable — and the names an existing
`.agentmarshal/switches.toml`'s entries are checked against SHALL be
that same set. The reason SHALL pass the parser's own rule:
non-empty, at most 1000 characters, the forgeable-text rule. An
existing `.agentmarshal/switches.toml` SHALL be parsed by the shared
parser before the task is opened: a file the parse refuses SHALL be
refused naming it, and an extension whose entry is already `off`
SHALL be refused naming the task that switched it off. Every refusal
before the task is opened SHALL write nothing — no task is opened and
no file changes.

#### Scenario: a name the working tree does not declare is refused before anything is written
- **WHEN** `extension switch off` names an extension
  `.agentmarshal/extensions/` does not declare
- **THEN** it is refused saying so, and no task is opened and no
  switches file is written

#### Scenario: a reason outside its rule is refused before anything is written
- **WHEN** `--reason` is empty, over 1000 characters or carries a
  forgeable character
- **THEN** the command refuses naming why, and no task is opened and no
  file changes

#### Scenario: a malformed switches file is refused naming it and nothing is written
- **WHEN** the working tree's `switches.toml` is refused by the parse
- **THEN** the refusal names the file, and no task is opened and the
  file is unchanged

#### Scenario: an extension already switched off is refused naming the task that switched it off
- **WHEN** the file's entry for the extension is already `off`
- **THEN** the refusal names the task that switched it off, and no task
  is opened and the file is unchanged

#### Scenario: a file-form extension is a shared extension the command switches off
- **WHEN** the working tree declares the extension as `<name>.toml`
  alone
- **THEN** the command opens the task and writes the switch the same
  way

#### Scenario: a declared extension whose manifest cannot be read is switched off
- **WHEN** the name is enumerated under `.agentmarshal/extensions/`
  but its manifest cannot be read — a directory form whose declared
  `bin/` file is missing, or a name claimed in both forms
- **THEN** the command opens the task and writes the switch the same
  way

#### Scenario: a link entry's name is a shared extension the command switches off
- **WHEN** the working tree declares the extension through a
  symbolic-link entry under `.agentmarshal/extensions/` — the
  directory form or the file form linked
- **THEN** the command opens the task and writes the switch the same
  way

#### Scenario: a file whose other entry names a linked extension is accepted
- **WHEN** an existing `.agentmarshal/switches.toml` carries an entry
  for an extension the working tree declares through a link
- **THEN** the parse accepts the file and the command proceeds — the
  names the entries are checked against are the enumerated set

### Requirement: the switches file keeps its text and is replaced atomically

The command SHALL keep the existing file's text and change only what
the switch needs: an extension already carrying an `on` entry SHALL
have the switch's own key/value lines inside that entry's
`[switches.<name>]` table replaced by the off entry's — the header,
every other key the entry carries and the file's other content kept —
and any other extension SHALL gain a new `[switches.<name>]` table
appended after the file's existing content. An `on` entry the command
cannot locate and bound on its own lines — a header or key spelled
with escapes or in any form other than a plain bare, basic or literal
key, a header-less form such as an inline table or dotted keys, a
multi-line value inside it holding a line that reads as a table
header — SHALL be refused before any task is opened, on one line
naming the file and saying the entry cannot be rewritten by this
command and must be switched off by editing the file in an
operational task; nothing is written. The `reason` SHALL be written
as a TOML basic string with every character that needs escaping
escaped. The whole new text SHALL be parsed by the shared parser
before the file is replaced — a text the parse refuses writes
nothing — and the file SHALL be replaced atomically: a temporary file
in `.agentmarshal/` renamed over it, an existing file's permission
bits kept and a created file's the usual creation mode masked by the
umask. A failure after the task is opened SHALL be reported on one
line naming the opened task and SHALL exit non-zero.

#### Scenario: an existing on entry's table is replaced and the file's other content is kept
- **WHEN** the file switches the extension `on` and carries other
  entries and comments
- **THEN** the extension's table is replaced by the off entry — the
  other entries, the comments and the file's order are as they were

#### Scenario: an on entry's other keys are kept through the rewrite
- **WHEN** the `on` entry carries a key beyond `state`, `task` and
  `reason` — a multi-line value whose `[`-led continuation lines are
  not table headers
- **THEN** the off entry is written inside the table and the other
  key's value is as it was

#### Scenario: an on entry the command cannot locate and bound on its own lines is refused before any task is opened
- **WHEN** an `on` entry is carried in a form the command cannot
  locate and bound on its own lines — a header or key spelled with
  escapes, a header-less form, or a multi-line value inside it
  holding a line that reads as a table header, like a last array
  element `["x"]` on its own line
- **THEN** the command refuses naming the file and saying the entry
  cannot be rewritten by this command and must be switched off by
  editing the file in an operational task, no task is opened and
  nothing is written

#### Scenario: a new entry is appended after the file's existing content
- **WHEN** the file switches another extension `on` and names this one
  not at all
- **THEN** this extension's `[switches.<name>]` table is appended and
  the file's existing content is unchanged ahead of it

#### Scenario: the new text is parsed back before it replaces the file
- **WHEN** the rewritten text fails the shared parser
- **THEN** nothing is written, and the failure is reported on one line
  naming the opened task with a non-zero exit

#### Scenario: the file is replaced by a temporary file renamed in the same directory
- **WHEN** the command writes the switches file
- **THEN** the new text is staged in a temporary file inside
  `.agentmarshal/` and renamed over the file — a reader never meets a
  half-written file

#### Scenario: a failure after the task is opened names the task on one line and exits non-zero
- **WHEN** the task opened but the switches file could not be written
- **THEN** the command reports the failure on one line naming the
  opened task and exits non-zero

### Requirement: `switch` is a group under `extension` and a sidecar opens no operational task

The `switch` group SHALL be registered under the existing `extension`
group with the `off` subcommand taking `off <name> --reason <text>`;
`extension trust`, `untrust` and `list` SHALL be unchanged, and no
other command changes. In a sidecar the command SHALL refuse with a
line saying operational tasks are not available in a sidecar, writing
nothing. Every value the command shows SHALL be escaped on display.

#### Scenario: the extension group takes switch off with a name and a reason
- **WHEN** the command-line parser is built
- **THEN** `agentmarshal extension switch off <name> --reason <text>`
  parses, and an unknown `switch` subcommand is refused

#### Scenario: a sidecar refuses saying operational tasks are not available
- **WHEN** `extension switch off` runs where the journal placement is a
  sidecar
- **THEN** it refuses with a line saying operational tasks are not
  available in a sidecar, and no task is opened and no file is written

#### Scenario: a value that could forge a line is escaped on display
- **WHEN** a refusal quotes a value carrying a forgeable character — a
  switches entry's name the parse refused
- **THEN** the displayed line carries the escape, not the character

### Requirement: `status` names each switched-off shared extension

`agentmarshal status` — the listing and the view of one task alike —
SHALL print on stderr, right after the lines naming where the journal,
the process log and the local state live, one line per shared
extension the working tree's `.agentmarshal/switches.toml` switches
off: `switched off: <name> since <task> (<reason>)` — ADR-0013
decision 17's "switched off since CR so-and-so, reason" — in the
enumeration's sorted order, every value the file carries escaped for
display. The file SHALL be the one `doctor` reads, read through the
same `read_switches` function and parsed against the shared extension
names `switches.shared_extension_names` enumerates for the working
tree's `.agentmarshal/extensions/`. The lines SHALL be owed in every
case where the paths printed — an empty journal's `No tasks.` and a
task lookup's refusal alike — printed before anything that can return
early. stdout SHALL be unchanged byte for byte. A project without the
file, or whose file switches no extension off, SHALL print nothing new
on stderr. A file the parse refuses SHALL be named on one stderr line
— `switches: unavailable (<reason>)`, the wording `doctor` reports the
same refusal with — and SHALL change neither `status`'s exit status
nor its stdout.

#### Scenario: the listing names each switched-off extension after the paths
- **WHEN** `status` runs in a project whose switches file switches a
  shared extension off
- **THEN** stderr carries `switched off: <name> since <task>
  (<reason>)` after the lines naming where the journal, the process
  log and the local state live

#### Scenario: the view of one task names each switched-off extension after the paths
- **WHEN** `status <task>` runs where the file switches a shared
  extension off
- **THEN** stderr carries the `switched off:` line after the paths

#### Scenario: the lines are owed wherever the paths printed — an empty journal and a failed lookup alike
- **WHEN** `status` lists an empty journal, or `status <task>` names a
  task the journal does not hold, where the file switches an extension
  off
- **THEN** the `switched off:` line still prints after the paths —
  before `No tasks.`, before the lookup's refusal

#### Scenario: a project without the file prints nothing new
- **WHEN** `status` runs — either form — where no `switches.toml`
  exists
- **THEN** stderr carries no `switched off:` line and nothing else new

#### Scenario: an extension switched on or with no entry prints nothing new
- **WHEN** the file switches one extension `on` and names another not
  at all
- **THEN** neither gains a line and stderr reads as before

#### Scenario: a file the parse refuses is named on one line and changes neither the exit nor stdout
- **WHEN** the working tree's `switches.toml` is refused by the parse
- **THEN** one `switches: unavailable (<reason>)` line names it after
  the paths, and `status`'s exit status and stdout are unchanged

#### Scenario: a value the file carries is escaped on display
- **WHEN** a switched-off entry's name carries a forgeable character
- **THEN** the displayed line carries the escape, not the character

#### Scenario: stdout stays byte for byte what it was
- **WHEN** `status` runs — either form — with or without a switches
  file
- **THEN** stdout is byte for byte what the command printed before the
  lines were added

### Requirement: the working tree's shared extension names are enumerated by one function

The set a shared extension name belongs to — the names the working
tree's `.agentmarshal/extensions/` declares — SHALL be enumerated by
one function, `switches.shared_extension_names`: a `<name>.toml` entry
the file form, a `<name>/` entry the directory form, a symbolic-link
entry kept under the name it carries with `.toml` removed, a name
found in more than one form enumerated once, an entry that is none of
these not an extension, and a managed path that is no directory
enumerating no names — whether or not the manifest under a name reads,
so a broken extension stays switchable. `doctor` SHALL enumerate
through it, its output unchanged, and `status`'s switches read SHALL
check the file's entries against the names it returns.

#### Scenario: doctor enumerates through the shared function
- **WHEN** `doctor` lists the working tree's extensions
- **THEN** the names come from `shared_extension_names` — the file
  form, the directory form and a link's name alike — and its output is
  unchanged

#### Scenario: a name declared only through a link is a shared extension the file can switch off
- **WHEN** `status` runs where an extension exists only as a
  symbolic-link entry and the file switches it off
- **THEN** its `switched off:` line prints

### Requirement: a stage with no declared network runs in a new user and network namespace

On Linux, a stage whose manifest does not declare `network = true`
SHALL run with no network the stage can reach: the stage's own child
SHALL enter a new user and network namespace —
`os.unshare(CLONE_NEWUSER | CLONE_NEWNET)` after `fork` and before
`execve`, `deny` written to `/proc/self/setgroups` and a one-line
identity mapping of the caller's uid and gid written to
`/proc/self/uid_map` and `/proc/self/gid_map` — applied by the core
itself, never a wrapper process, a shell or a tool looked up on
`PATH`. In the same child, still before `execve`, every capability
the new user namespace granted SHALL be dropped — they otherwise
survive `execve` (user_namespaces(7)) and let the stage undo the
enforcement: the ambient set cleared (`PR_CAP_AMBIENT_CLEAR_ALL`),
the securebits `SECBIT_NOROOT | SECBIT_NOROOT_LOCKED |
SECBIT_NO_SETUID_FIXUP | SECBIT_NO_SETUID_FIXUP_LOCKED` and
`PR_SET_NO_NEW_PRIVS` set through `prctl`, `PR_CAPBSET_DROP` run for
each capability up to `/proc/sys/kernel/cap_last_cap`, and `capset`
clearing the effective, permitted and inheritable sets — all through
libc. A stage whose manifest declares `network = true` SHALL run
as before. A capability drop that fails SHALL name every guarantee
the child was asked to enforce not enforced with the reason
`capabilities could not be dropped: <reason>` — the child must not
exec silently still holding capabilities; and namespaces this
platform or environment cannot provide SHALL NOT stop the stage: the
stage still runs, and what could not be enforced is named under the
naming requirement.

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

### Requirement: a guarantee the core cannot enforce is named, never silently weakened

The core SHALL answer once per run — a probe in a throwaway child
running the real sequence, the capability drop included, and dying
with it, its verdict cached — which guarantees this platform and
environment allow, asked at the first stage that runs so the answer
precedes the stage rather than following it. Each guarantee a stage
is owed that the probe or the stage's own setup could not enforce
SHALL be named on one note line for the stage, each with its reason
— `not enforced: <guarantee> (<reason>)`, as `network`,
`read-only candidate` and `writes beyond the candidate` are named —
and the stage SHALL still run; a guarantee enforced SHALL NOT be
mentioned, so a platform enforcing everything shows unchanged
output. A setup step that fails in the stage's own child after the
probe allowed it SHALL be named the same way: before `execve` the
child reports each asked-for guarantee's outcome over a dedicated
pipe the parent creates — the write end close-on-exec since
`os.pipe()` made it, never named in `pass_fds` which would make
it inheritable — so the spawn's own descriptor closing closes it
before `execve` and the extension's code never holds it — and the
parent reads it to EOF; a report
that never arrives cannot vouch for a guarantee and names it not
enforced — never a silent weakening, and never a byte of the
stage's own output read as a core message; a capability drop that
fails is such a step, named on every guarantee the child was asked
to enforce. A stage that does not run at all SHALL carry no
isolation note.

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
- **THEN** the failure is reported on the child's dedicated pipe —
  a channel the extension's code cannot reach — and the guarantee
  is named `not enforced` the same way

#### Scenario: a stage's own output never carries the setup's report
- **WHEN** a stage's output carries a line shaped like a setup
  report — text only the child's report pipe may carry
- **THEN** the line is framed as the stage's own output like any
  other and names no guarantee not enforced

#### Scenario: a capability drop that fails names every guarantee the child was asked to enforce
- **WHEN** the probe allowed the guarantees but the stage child's
  capability drop fails
- **THEN** each guarantee the child was asked to enforce is named
  `not enforced: <guarantee> (capabilities could not be dropped:
  <reason>)` — the child does not exec silently with capabilities —
  and the stage still runs

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

### Requirement: an accepted pause stands down a pre-gate-stop stage's pause for the accepted extension and commit

At `--phase pre-gate`, when a `pre-gate-stop` stage's decision is
`failed`, `did-not-finish` or `not-run`, the command SHALL look in the
task's acceptance records — read through `read_records` from the
journal the placement names, never a second parser — for an
`acceptance` record carrying `accepted_pause` naming the stage's
extension and `accepted_commit` equal to the commit the run resolved
(ADR-0013 decision 5, ADR-0022 section 2); where several match, the
latest in journal order applies. An acceptance bound to another
commit, naming another extension, or of another form — `findings` or
`operational` — SHALL NOT count. With a match the stage's result line
SHALL keep its outcome and add `, pause accepted by <party> (<reason>)`
— `<party>` the record's `accepted_by`, `<reason>` the record's
`reason`, each escaped for display — and the stage SHALL NOT pause the
process. The stage's `extension-event` SHALL carry the decision it
carries today, and its `reason` SHALL name the acceptance record: the
reason it carries today followed by `; pause accepted by acceptance
record <id>`, the record's id as `read_records` yields it — or that
clause alone where the stage's reason is empty. A `checked` stage and a
`switched-off` stage SHALL NOT consult an acceptance — a checked
stage's line never mentions one — and neither SHALL a `pre-gate-warn`
stage nor a `post-gate` stage, whose outcomes are unchanged. The
journal SHALL be read lazily, at the first `pre-gate-stop` stage whose
decision calls for it, so a run that pauses nothing never opens it; a
journal that cannot be read SHALL be named on one stderr line and
every pause SHALL stand — the fallback never lifts a pause.

#### Scenario: an accepted pause lets the process continue naming who accepted
- **WHEN** a `pre-gate-stop` stage's decision is `failed` and the task
  holds an acceptance carrying `accepted_pause` naming that extension
  and `accepted_commit` equal to the commit the run resolved
- **THEN** the result line reads `<name>: failed (exit <n>), pause
  accepted by <party> (<reason>)` naming the record's `accepted_by`
  and `reason`, no pause line is printed and the command exits 0

#### Scenario: an accepted pause stands down a did-not-finish or not-run stage the same way
- **WHEN** a `pre-gate-stop` stage's decision is `did-not-finish` or
  `not-run` and a matching acceptance stands
- **THEN** the result line keeps its outcome and adds the
  `pause accepted by <party> (<reason>)` suffix, and the command exits
  0 when no other stage pauses

#### Scenario: the latest matching acceptance in journal order is the one named
- **WHEN** two acceptances carry `accepted_pause` for the stage's
  extension and `accepted_commit` equal to the resolved commit
- **THEN** the result line and the extension-event name the later
  record

#### Scenario: an acceptance bound to another commit does not count
- **WHEN** the task's `accepted_pause` acceptances for the extension
  bind commits other than the one the run resolved
- **THEN** the stage pauses as before and the command exits 3

#### Scenario: an acceptance naming another extension does not count
- **WHEN** the task's `accepted_pause` acceptance at the resolved
  commit names a different extension
- **THEN** the stage pauses as before and the command exits 3

#### Scenario: an acceptance of another form does not count
- **WHEN** the task's acceptances at the resolved commit carry
  `findings` or `operational` and none carries `accepted_pause` for the
  extension
- **THEN** the stage pauses as before and the command exits 3

#### Scenario: an accepted pause lifts no other stage's pause
- **WHEN** one `pre-gate-stop` extension's pause is accepted and a
  second `pre-gate-stop` stage pauses with no matching acceptance
- **THEN** the accepted stage's result line carries the
  `pause accepted by` suffix, the second stage's pause stands and the
  command exits 3

#### Scenario: a checked stage's line never mentions an acceptance
- **WHEN** a `pre-gate-stop` stage's decision is `checked` and a
  matching acceptance stands
- **THEN** the result line is `<name>: checked` with no suffix

#### Scenario: a pre-gate-warn stage is unchanged by an acceptance
- **WHEN** a `pre-gate-warn` stage's decision is `failed` and an
  `accepted_pause` acceptance names the extension at the resolved
  commit
- **THEN** the warning prints, no `pause accepted by` suffix appears
  and the command exits 0

#### Scenario: a post-gate stage is unchanged by an acceptance
- **WHEN** a `post-gate` stage's decision is `failed` and an
  `accepted_pause` acceptance names the extension at the resolved
  commit
- **THEN** its result line is unchanged and the command exits 0

#### Scenario: a switched-off stage is unchanged by an acceptance
- **WHEN** a `pre-gate-stop` extension is switched off at the base and
  an `accepted_pause` acceptance names it at the resolved commit
- **THEN** the result line is `<name>: switched off (<task>,
  <reason>)` with no `pause accepted by` suffix and no pause

#### Scenario: the extension-event of an accepted pause names the acceptance record
- **WHEN** an accepted `pre-gate-stop` stage's result is appended to
  the process log
- **THEN** the event carries the decision it carries today and a
  `reason` ending `pause accepted by acceptance record <id>` naming
  the record's id

#### Scenario: a record's values are escaped on display
- **WHEN** an acceptance's `accepted_by` or `reason` reaching the
  suffix carries a forgeable character
- **THEN** the displayed line carries the escape, not the character

#### Scenario: a journal that cannot be read names it and every pause stands
- **WHEN** a `pre-gate-stop` stage's decision calls for the acceptance
  read and the journal cannot be read
- **THEN** one stderr line names the journal, the stage's result line
  carries no `pause accepted by` suffix, the pause stands and the
  command exits 3

### Requirement: the stage run is one function both commands call

The run `stage run` performs SHALL be one function —
`stages.run_stages` — taking the resolved placement, the clone's local
state, the task id, the commit, the base, the phase and stderr
explicitly, never a parsed-arguments namespace, and returning a small
result: `status`, the exit status the invocation ends with (0, 1 when
the run's own machinery refused it, 3 when a `pre-gate-stop` stage
paused); `pauses`, the `pre-gate-stop` stages that paused as
`<name>: <result>` entries in run order, unprinted; and `plan_empty`,
whether the run reached the plan and the phase matched no stage. Every
line the other requirements pin SHALL be printed by the runner except
the per-entry pause lines and the no-stage line, which the caller
renders: `stage run`'s wrapper SHALL print
`stage run: the process is paused before the gate — <entry>` per pause
and `stage run: no shared extension declares a <phase> stage` on an
empty plan, so the command's output and exit statuses are unchanged
byte for byte.

The runner SHALL take a quiet mode — `quiet=True` — which `complete`
invokes with: under it a plan matching no stage SHALL print nothing at
all — neither the no-stage line the caller already withholds nor the
operational line, which under the quiet mode SHALL print only where a
stage would otherwise have run — and the run's own refusals and
machinery diagnostics (a refusal of the run's inputs, a switches or
trust file the parse refuses, a process log or journal that cannot be
written) SHALL be reported under the calling command's own prefix
rather than `stage run:`. The stage lines — the output frames, the
result lines, the `note:` lines, the `WARNING:` lines and the
operational line — SHALL keep the `stage run` voice either way.

#### Scenario: stage run's transcript is unchanged by the shared runner
- **WHEN** `stage run` runs stages to a pause — or matches no stage
- **THEN** the pause lines read `stage run: the process is paused
  before the gate — <entry>` and the exit is 3, and the empty run
  prints `stage run: no shared extension declares a <phase> stage` —
  as before the runner was shared

#### Scenario: both commands go through the one runner
- **WHEN** `stage run` runs and `complete --task --commit --base`
  completes a candidate
- **THEN** each invocation is a call to `stages.run_stages` — complete
  calls it once for `pre-gate` and, after the `completed` record, once
  for `post-gate`

### Requirement: `complete` runs the `pre-gate` stages before its gate check

`agentmarshal complete --task <id> --commit <rev> --base <ref>` in the
embedded placement SHALL resolve `--commit` and `--base` to commits the
way the gate resolves them — a reference that does not resolve keeps
the refusal `complete` gives it today, issued before any extension work
— and SHALL invoke `run_stages` for `pre-gate`, quiet, with the task
and the resolved commits — after the task's open state is established,
so a closed task's refusal still precedes any extension work, and
before the gate is evaluated and before anything is written (ADR-0013
decision 2). The run's own lines keep the `stage run` voice — the stage
output frames, result lines, notes and warnings print exactly as
`stage run` prints them — while the run's refusals and machinery
diagnostics carry `complete`'s prefix as the quiet mode states; the
pause lines are the pause requirement's to render. A run whose own
machinery refused — the exit-1 outcome — SHALL refuse the completion on
one `complete:` line with the same status, writing nothing. A plan
matching no stage SHALL print nothing — a project whose shared
extensions declare no `pre-gate` stage reads exactly as `complete`
reads today, on an ordinary candidate and on an operational one alike.
The findings lane (`complete --findings`, which takes no candidate) and
the sidecar placement SHALL invoke no stage at all.

#### Scenario: the pre-gate stages run before the gate's transcript and before any write
- **WHEN** `complete` runs in a project whose base declares a
  `pre-gate` stage
- **THEN** the stage's lines precede the gate's transcript on stdout,
  and a run that ends in a refusal writes nothing

#### Scenario: a run whose machinery refused refuses the completion
- **WHEN** the `pre-gate` run's own machinery refuses — a manifest the
  base cannot parse, a trust file that cannot be read
- **THEN** the run's refusal is reported under `complete`'s prefix,
  `complete` prints one `complete:` refusal line, exits with the run's
  status and writes nothing

#### Scenario: a plan matching no stage prints nothing
- **WHEN** `complete` runs in a project whose shared extensions declare
  no `pre-gate` stage — or none at all
- **THEN** stdout and stderr read exactly as `complete` reads today —
  no stage line, no no-stage line

#### Scenario: an operational change's completion skips the pre-gate stages
- **WHEN** `complete` runs on a candidate the gate's operational lane
  admits — a switches-only diff under a contract scoping exactly
  `.agentmarshal/switches.toml` — where a shared extension declares a
  `pre-gate` stage
- **THEN** the invocation prints the operational line, runs no stage
  and the completion proceeds — a broken extension cannot block its
  own switching off

#### Scenario: an operational change with no stage to skip prints nothing
- **WHEN** `complete` runs on a candidate the operational lane admits
  in a project whose shared extensions declare no `pre-gate` stage —
  or none at all
- **THEN** no extension line prints at all — no stage line, no
  operational line — and the completion proceeds

#### Scenario: an unresolvable ref is refused as complete refuses it today
- **WHEN** `complete` is invoked with a `--commit` or `--base` that
  does not resolve
- **THEN** the refusal is the resolution failure `complete` reports
  today, before any extension line — none is printed — and nothing is
  written

#### Scenario: the findings lane invokes no stage
- **WHEN** `complete --findings` runs in a project whose base declares
  stages
- **THEN** no stage runs, no stage line prints and no extension event
  is written

#### Scenario: a sidecar invokes no stage
- **WHEN** `complete` runs where the journal placement is a sidecar
- **THEN** no stage runs at either point — the advisory completion
  reads as it reads today

#### Scenario: the stage's environment is the resolved candidate's
- **WHEN** `complete` runs a `pre-gate` stage for
  `--commit <ref> --base <ref>`
- **THEN** the stage's environment carries `AGENTMARSHAL_PHASE`
  `pre-gate`, `AGENTMARSHAL_TASK` the task, `AGENTMARSHAL_COMMIT` the
  resolved candidate commit and `AGENTMARSHAL_BASE` the resolved merge
  base — `complete` resolves the refs first and hands the runner the
  resolved commits — and its working directory is a snapshot of the
  resolved candidate

### Requirement: a `pre-gate-stop` pause refuses `complete` only while the candidate is not merged

When the `pre-gate` run pauses — the exit-3 outcome — `complete`
SHALL decide whether the candidate is already merged into the target
branch: `git merge-base --is-ancestor` of the resolved candidate into
the resolved `--target`, in the journal's repository, the target
resolved to a commit exactly as the gate resolves the refs. `--target`
names the branch the candidate merges into — distinct from `--base`,
which stays the merge base the gate diffs against, since a merge
wrapper passes the pre-merge merge base even after the merge. With no
`--target` given, or with a target the check cannot answer for — a
reference that will not resolve, a git that will not run — the
candidate SHALL read as not merged: the pause stands rather than being
silently lifted. While the candidate is not an ancestor of the
resolved target, the completion SHALL be refused: the stage lines
stand as printed, one stderr line — `complete: the completion is
paused before the gate — <entry>; …` — names every paused stage's
result in run order, nothing is written and the exit status is the
pause's own, 3. Once the candidate is an ancestor of the resolved
target, each pause SHALL instead be reported on one stderr line —
`complete: WARNING: extension at pre-gate-stop — <entry> — the
candidate is already merged into the target` — and the completion
SHALL proceed to the gate and, when the gate passes, write
`completed`. An accepted pause stands down in `complete` exactly as
`stage run` reads it — the runner's own reading of the task's
acceptances, not a second one.

#### Scenario: a pause while the candidate is not an ancestor refuses the completion
- **WHEN** a `pre-gate-stop` stage pauses and the candidate is not an
  ancestor of the resolved `--target` — or no `--target` is given
- **THEN** the stage lines print, one stderr line says the completion
  is paused before the gate naming the paused stage's result, nothing
  is written and `complete` exits 3 — the pause status `stage run`
  uses

#### Scenario: the pause line names every paused stage
- **WHEN** two `pre-gate-stop` stages pause on a candidate the target
  does not contain — or cannot resolve
- **THEN** the one refusal line names both `<name>: <result>` entries
  in run order

#### Scenario: a pause on an already-merged candidate is a warning
- **WHEN** a `pre-gate-stop` stage pauses and the candidate is an
  ancestor of the resolved `--target`
- **THEN** one `complete: WARNING:` line per paused stage names it and
  says the pause does not apply, no pause line is printed and the
  completion proceeds to the gate, writing `completed` when the gate
  passes

#### Scenario: an accepted pause stands down in complete as in stage run
- **WHEN** a `pre-gate-stop` stage pauses and the task holds an
  acceptance carrying `accepted_pause` naming the extension and
  `accepted_commit` equal to the resolved candidate
- **THEN** the result line carries the `pause accepted by` suffix, no
  pause line and no warning is printed, and the completion proceeds

### Requirement: `complete` runs the `post-gate` stages after `completed` is written

Once `complete` has written the `completed` record — and after
`complete`'s own output — it SHALL invoke the same `run_stages` for
`post-gate`, quiet, with the task and the resolved commits. The run is
a notification (ADR-0013 decision 4): its outcome SHALL change neither
the record nor the exit status. A completion that wrote nothing — a
refused gate, a standing pause — SHALL not invoke it.

#### Scenario: the post-gate stages run after the completed record is written
- **WHEN** `complete` succeeds in a project whose base declares a
  `post-gate` stage
- **THEN** the stage's lines follow `complete`'s own output, and its
  `extension-event` lands in the process log

#### Scenario: a post-gate result changes neither the record nor the exit status
- **WHEN** a `post-gate` stage fails or does not run
- **THEN** `complete` still exits 0, the `completed` record stands and
  the stage's result line prints as the notification it is

### Requirement: the clone's personal extensions' stages run on a workstation

`stage run` — and `complete` through the shared runner — SHALL also run
the clone's personal extensions' declared stages: directory-form
manifests under `.git/agentmarshal/extensions/<name>/`, located through
`LocalState.extensions`, read from that directory and never the base,
needing no grant, under the same `_run_stage` path — snapshot, timeout,
isolation — its `command` launched directly as a program, since a
personal extension may be written in any language (ADR-0013 decision 13
as amended); a command file without the executable bit SHALL be `not
run` naming why. A trust file that cannot be read SHALL matter only
where a shared stage is planned — grants concern shared stages alone —
and change nothing about a run of personal stages alone. In CI (`CI`
equals `true`) no personal stage is planned and nothing personal is
printed.

#### Scenario: a personal extension's stage runs on a workstation without a grant

On a workstation, a personal extension with a `pre-gate` stage declared
runs it under the same snapshot, timeout and isolation rules as a
shared stage — no trust grant is asked — and its frames and result line
print at its name-sorted slot after the shared stages.

#### Scenario: a personal stage's command runs directly as a program

A personal stage's `command` — an executable shell script, say — is
exec'd itself, not fed to the core's interpreter; a script that would
fail under that interpreter prints `checked (personal)`.

#### Scenario: a non-executable personal command file is not run naming why

A personal stage whose `command` file lacks the executable bit prints
`<name>: not run (command <path> is not executable) (personal)` and —
a `pre-gate-stop` — pauses the run the usual way.

#### Scenario: an unreadable trust file does not fail a personal-only run

With only personal stages planned, a `trust.toml` the grants parser
refuses prints nothing about the trust file: the personal stages run
and the run's outcome is decided by them alone.

#### Scenario: an unreadable trust file still fails a run planning a shared stage

With a shared stage planned, the same refusal prints the one
`stage run: <trust file>: <reason>` line, the shared stage owes no
result line, and the command exits 1 — the personal stages still
running, a grant never asked of them.

#### Scenario: the clone's directory is what runs, never the base

A personal extension created after the base commit — never committed —
still runs, and what runs is the `manifest.toml` in
`.git/agentmarshal/extensions/<name>/` as the clone holds it, not
anything read from a tree.

#### Scenario: a personal stage is invoked at the phase its manifest declares

A personal manifest declaring `pre-gate-warn` runs when `stage run`
is invoked for `pre-gate`; one declaring `post-gate` does not.

#### Scenario: no personal stage is planned or printed in CI

With `CI` equal to `true`, a run with a personal extension prints no
personal result line, no note and no mark; the transcript reads as if
the directory were absent.

#### Scenario: complete runs the personal stages through the shared runner

`complete` on a workstation plans the personal stages at the phase each
declares — pre-gate before the gate and before any record write,
post-gate quietly after the completed record is written — with the same
output and pause semantics as `stage run`.

#### Scenario: an operational change runs no personal stage

An operational target's stages lane runs no personal stage — no personal
line or event appears for a run that stages nothing.

### Requirement: a personal manifest that cannot be read is named on one line

A personal manifest that cannot be read — invalid TOML, a schema or
shape violation, a link at the directory or the manifest, a named file
missing — SHALL be named on one line `<name>: not run (<reason>)
(personal)` and run no stage, never failing the run; an `extensions`
path that is no directory or cannot be listed SHALL be named on one
`stage run: note:` line.

#### Scenario: a personal manifest that cannot be read is named on one line

A personal directory holding no `manifest.toml` — or one that does not
parse — prints `<name>: not run (<reason>) (personal)` and the run
continues past it to the other stages.

#### Scenario: a personal manifest of schema 1 is refused naming the schema

A personal manifest declaring `schema = 1` prints `<name>: not run
(the directory form requires a manifest of schema 2; '<name>' declares
schema 1: <path>) (personal)` — the reason naming the declared schema,
not the schema-2 fields a shared parse would call missing.

#### Scenario: an extensions directory that cannot be enumerated is named on one note line

An `extensions` path that exists and is not a directory, or a listing
that fails, prints one `stage run: note:` line naming the reason and
the run continues with the shared stages.

### Requirement: every personal stage's result is marked personal

Each personal stage SHALL print its one result line as `<name>:
<result> (personal)` — the shared result vocabulary with ` (personal)`
appended — and a `pre-gate-stop` personal stage whose decision is not
`checked` SHALL pause the local run like a shared one, the pause entry
carrying the mark; a `pre-gate-warn` failure warns the same way.

#### Scenario: a checked personal stage's line is marked personal

A personal `pre-gate` stage that exits 0 prints `<name>: checked
(personal)` as its one result line.

#### Scenario: a failed personal stage's line is marked personal

A personal `pre-gate` stage that exits 1 prints `<name>: failed (exit 1)
(personal)`.

#### Scenario: a pausing personal pre-gate-stop stage pauses the local run marked personal

A `pre-gate-stop` personal stage that exits 1 makes `stage run` refuse
the gate — exit 3 — and its line in the pause listing carries the mark:
`mycheck: failed (exit 1) (personal)`; an acceptance naming the
extension and the run's commit stands it down the shared way.

#### Scenario: a personal pre-gate-warn failure warns marked personal

A `pre-gate-warn` personal stage that exits 1 prints `failed (exit 1)
(personal)` and adds `<name>: failed (exit 1) (personal)` to the
warnings; the run does not pause.

#### Scenario: a personal pause refuses complete while the candidate is not merged

`complete` on a workstation whose personal `pre-gate-stop` stage pauses
refuses with exit 3, prints the pause naming the marked entry, writes
nothing, and — once the candidate is an ancestor of the target — warns
and proceeds exactly as for a shared stage.

### Requirement: a personal extension named like a shared one is not run

A personal extension whose name a shared extension at the base also
declares SHALL NOT run — the shared extension wins — and SHALL be named
on one line for the invocation: `<name>: not run (a shared extension of
this name wins) (personal)`.

#### Scenario: a personal extension named like a shared one is not run and is named on one line

A personal `openspec` where a shared `openspec` is declared at the base
prints `openspec: not run (a shared extension of this name wins)
(personal)` at its sorted slot and runs no stage — whether the shared
extension runs, is switched off or is ungranted.

### Requirement: an extension-level line is owed only at a declared phase

An extension-level line — the collision line, `disabled`, `skipped for
this run`, the refused-manifest `not run` — SHALL print only when the
extension declares a stage in the phase being run: an extension with
no stage for the phase owes no line at all. For a manifest the reader
refuses, the phases SHALL be taken from the raw manifest table where
they can be established; where they cannot, the refusal line stands at
every invocation rather than being silently dropped.

#### Scenario: an extension-level line is owed only at a declared phase

A personal extension declaring only a `pre-gate-stop` stage, disabled
or named in `--skip-ext`, prints its `disabled (personal)` or `skipped
for this run (personal)` line at a `pre-gate` invocation and nothing
at `post-gate`; the same holds for the collision line.

#### Scenario: a refused manifest's line follows the phases its raw table names

A refused manifest whose raw `[[stage]]` entries still read prints its
`not run (<reason>) (personal)` line only where one of those phases is
invoked; a manifest whose table does not parse at all prints the line
at every invocation.

### Requirement: a personal manifest carries no footprint, documents or artifacts

A personal manifest SHALL carry no `footprint`, `documents` or
`artifacts` (ADR-0013 decision 10). One that declares any SHALL be
refused: `stage run` prints `<name>: not run (<reason>) (personal)` on
one line and runs no stage of it, and `doctor` fails its manifest
check naming the field.

#### Scenario: a personal manifest declaring footprint, documents or artifacts is refused and does not run

A personal manifest carrying `footprint`, or `documents`, or
`artifacts`, is named on one `not run` line each with the field in the
reason and runs no stage — the refusal is at the manifest, not the run.

#### Scenario: doctor fails the check of a personal manifest carrying a forbidden field

`doctor` reports `FAIL extension manifest <name> (personal)` with the
forbidden field named in the detail.

### Requirement: a personal extension is skippable for a run and switchable off

`stage run --skip-ext <name>` and `complete --skip-ext <name>` SHALL
skip a personal extension for that run, printing `<name>: skipped for
this run (personal)`; `extension disable <name>` SHALL write `state =
"off"` under `[switches.<name>]` in the clone's
`.git/agentmarshal/switches.toml` and `extension enable <name>` SHALL
remove the entry — a rewrite changing only the named entry, other
entries and keys the format does not name standing as they were; a
disabled extension prints `<name>: disabled
(personal)` and does not run.

#### Scenario: stage run --skip-ext skips a personal extension for that run

`stage run --skip-ext mycheck` prints `mycheck: skipped for this run
(personal)`, runs no stage of it, and the next run without the flag
runs it again — nothing is written.

#### Scenario: complete --skip-ext skips a personal extension for that run

`complete --skip-ext mycheck` skips the extension at both of the run's
phases and completion proceeds; `complete --findings` takes no
`--skip-ext` and refuses the flag on one line.

#### Scenario: extension disable writes the off switch to the clone's switches.toml

`extension disable mycheck` writes `format = 1` and `[switches.mycheck]
state = "off"` — plus `reason` when `--reason` is given — to the
clone's `.git/agentmarshal/switches.toml`, names the file, and prints
`disabled mycheck`.

#### Scenario: a disabled personal extension prints disabled (personal) and does not run

A run with `mycheck` switched off prints `mycheck: disabled (personal)`
at its slot, runs no stage of it, and does not pause.

#### Scenario: extension enable removes the switch and the extension runs again

`extension enable mycheck` removes the entry, names the file, prints
`enabled mycheck`, and the next run runs the stage; `enable` on an
extension that is not disabled refuses on one line and writes nothing.

#### Scenario: a rewrite changes only the named switch entry

With `alpha` and `beta` switched off — `beta`'s entry also carrying a
key the format does not name — `extension enable alpha` rewrites the
file so that, parsed, it differs only in `alpha`'s entry: `beta`'s
state, reason and extra key stand, and an entry for an extension the
clone no longer holds stands untouched.

### Requirement: the personal switches file

The clone's `.git/agentmarshal/switches.toml` SHALL carry `format = 1`
and a `[switches]` table holding per personal extension a `state` of
`on` or `off` and an optional `reason` passing the forgeable-text rule;
other keys and entries naming no personal extension pass unread. A
missing file means every personal extension is on; a file the parse
refuses is named on one line, every personal extension on.

#### Scenario: a missing personal switches file means every personal extension is on

A clone with a personal extension and no `switches.toml` runs the
extension's stages and prints no switch line.

#### Scenario: a personal switches file that cannot be read leaves every personal extension on

A `switches.toml` that is no valid file for the format prints one
`stage run: note:` line naming the reason and the run proceeds with
every personal extension on.

#### Scenario: an entry naming no personal extension and keys beyond the shape pass unread

A switch for a name the clone no longer holds, or an entry with a key
the format does not name, is read past — the file neither fails the
parse nor switches a shared extension.

### Requirement: a shared extension is never named in a personal switch

Naming a shared extension in `--skip-ext`, `extension disable` or
`extension enable` SHALL be refused on one line saying a shared
extension is switched off only by an operational task (`extension
switch off`); `disable` and `enable` write nothing, and `--skip-ext`
refuses the run before any stage is planned.

#### Scenario: a shared name in --skip-ext is refused before any stage runs

`stage run --skip-ext openspec` — where `openspec` is a shared
extension — prints `openspec: a shared extension is switched off only
by an operational task (extension switch off)` and refuses the run;
nothing is planned or logged.

#### Scenario: a shared name in extension disable is refused and nothing is written

`extension disable openspec` prints the same refusal naming the
extension, exits 1 and creates or changes no `switches.toml`.

#### Scenario: a shared name in extension enable is refused

`extension enable openspec` prints the refusal, exits 1 and writes
nothing.

#### Scenario: a name no personal extension declares is inert for --skip-ext and refused by disable

`--skip-ext` naming an extension that exists nowhere prints nothing and
runs what it would run; `extension disable` of it prints `<name> is not
a personal extension` and writes nothing.

### Requirement: doctor lists personal extensions with the personal scope

`doctor` SHALL print one line per personal extension after the shared
lines — `extension <name>: personal scope, directory form, manifest
schema <n>, stages: <modes>, ext kinds: <kinds>` — `disabled` appended
when the switch is off, and SHALL run an `extension manifest <name>
(personal)` check per extension, failed on a manifest it refuses.

#### Scenario: doctor lists a personal extension with the scope personal

A personal `mycheck` prints `extension mycheck: personal scope,
directory form, manifest schema 2, stages: <modes>, ext kinds:
<kinds>` after the shared lines, and an `extension manifest mycheck
(personal)` check passes or fails on the same manifest.

#### Scenario: doctor names a disabled personal extension

With `mycheck` switched off its line reads `extension mycheck: personal
scope, directory form, manifest schema 2, stages: <modes>, ext kinds:
<kinds>, disabled`.

#### Scenario: a personal switches file the parse refuses is named on one line and fails nothing

A malformed `switches.toml` prints `personal switches: unavailable
(<reason>)` after the extension lines, keeps every extension shown as
not disabled, and fails no check for it.

#### Scenario: doctor lists personal extensions when the shared directory refuses

A `.agentmarshal/extensions/` the enumeration refuses — a link, say —
prints `extensions: unavailable (<reason>)` and the one failing
`extension manifests` check, and the personal lines and the `(personal)`
checks still follow: the personal scope is the clone's own and owes
nothing to the shared enumeration.

### Requirement: a clone with no personal extension prints exactly what it prints today

A clone whose `.git/agentmarshal/extensions/` is absent or holds no
extension SHALL get exactly the transcript it gets today: no result
line, note, section or check is owed to the personal scope,
`plan_empty` is unchanged, every existing line reads as it did, and the
gate is unchanged.

#### Scenario: a clone with no personal extension prints exactly what it prints today

`stage run`, `complete`, `doctor` and `status` on a clone with no
personal extension print byte-identically to before — shared lines
carry no mark, no personal line or check appears.

#### Scenario: the personal scope adds no mark to a shared stage's line

A shared stage's result line is unchanged — no `(personal)` mark, no
change to the shared result vocabulary — whether or not personal
extensions exist.

#### Scenario: a personal extension declaring no matching stage prints nothing

A personal extension whose manifest declares no stage for the invoked
phase prints nothing and adds no event.

### Requirement: a personal extension has no journal authority

A personal extension SHALL write no `ext` records — `record-ext`
accepts only kinds a shared extension declares, a personal manifest's
`[records]` entries never entering the accepted set — and nothing to
the journal; its `extension-event`s SHALL carry `scope` `personal`.

#### Scenario: record-ext refuses a kind only a personal manifest declares

`record-ext --kind mycheck/thing@1` — declared only by a personal
manifest — refuses the kind as undeclared and writes no record.

#### Scenario: a personal stage's extension-event carries the personal scope

A personal stage that runs writes an `extension-event` naming the
extension with `scope` `personal` and the decision and reason of the
outcome.

#### Scenario: a personal stage writes nothing to the journal

A run of personal stages appends no record and no `ext` record to the
journal; the process log gains only the stage's `extension-event`.
