# extension-stages Specification (delta)

## Purpose

The operational-lane exception of the invocation requirement said the
run prints one line and returns success before any manifest is read —
which placed it ahead of the `--skip-ext` refusal a shared name draws
everywhere else: on the lane, `stage run --skip-ext <shared>` printed
the operational line and exited 0. The exception now follows the
refusal, decided on the names the base's `extensions/` enumerates with
no manifest read, exactly as the code does.

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
manifest read for `--phase pre-gate` — and the `--skip-ext` refusal of
a shared name precedes the exception, decided on the names the merge
base's `.agentmarshal/extensions/` enumerates with no manifest read,
as "a shared extension is never named in a personal switch" states: on
a candidate the gate's own operational-lane predicate qualifies —
decided by the same function the gate uses, imported rather than
copied — the invocation SHALL print one line saying pre-gate stages do
not run on an operational change and SHALL run no stage, reading no
extension manifest and consulting no switch to decide one — no
extension event, no pause — returning success (ADR-0013 decision 17:
otherwise a broken extension blocks its own switching off). Extensions
SHALL run in the sorted order of their names, each extension's
matching stages in the order its manifest declares. A manifest the
base-tree reader refuses SHALL fail the command naming the extension
and its tree source. A file-form extension SHALL have no stage to run
— it declares no directory. A sidecar SHALL refuse: a stage's base is
a property of the embedded placement. An invalid task identifier SHALL
refuse before any manifest is read.

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

#### Scenario: a shared name in --skip-ext is refused before the operational-lane exception
- **WHEN** `stage run --phase pre-gate --skip-ext <name>` names a
  shared extension on a candidate the gate's operational lane admits
- **THEN** the run refuses with the shared-name refusal line — the
  operational line does not print, no manifest is read and no stage is
  planned
