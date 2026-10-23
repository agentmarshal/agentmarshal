# extension-stages Specification (delta)

## Purpose

ADR-0013 decision 17's exception on the stage side: on a candidate the
gate's operational lane admits, a `pre-gate` invocation runs no stage —
otherwise a broken extension blocks its own switching off. The
exception is stated on the requirements whose text would otherwise
promise the run: the invocation requirement, which has each manifest
read and each matching stage invoked, and the base-switches
requirement, which has each switched-off extension's stage report
`switched off`.

## MODIFIED Requirements

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
