# extension-stages Specification (delta)

## ADDED Requirements

### Requirement: the clone's personal extensions' stages run on a workstation

`stage run` — and `complete` through the shared runner — SHALL also run
the clone's personal extensions' declared stages: directory-form
manifests under `.git/agentmarshal/extensions/<name>/`, located through
`LocalState.extensions`, read from that directory and never the base,
needing no grant, under the same `_run_stage` path — argv, snapshot,
timeout, isolation. In CI (`CI` equals `true`) no personal stage is
planned and nothing personal is printed.

#### Scenario: a personal extension's stage runs on a workstation without a grant

On a workstation, a personal extension with a `pre-gate` stage declared
runs it under the same argv, snapshot, timeout and isolation rules as a
shared stage — no trust grant is asked — and its frames and result line
print at its name-sorted slot after the shared stages.

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
remove the entry; a disabled extension prints `<name>: disabled
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
