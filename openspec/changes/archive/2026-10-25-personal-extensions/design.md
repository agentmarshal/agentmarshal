# Design: personal-extensions

## Context

`run_stages` is the one runner — `stage run` and `complete` both call it,
per phase. A shared extension's manifest is read from the base tree
(`_base_extensions`), materialized into a temporary directory
(`_prepare_extension`, git-archive style, trust-grant checked off CI) and
run by `_run_stage`: the argv from the manifest, the candidate snapshot
as the stage's working directory, a timeout, the manifest's isolation
declared to `isolation.stage_setup`. The run prints one result line per
stage, writes one `extension-event` per stage, and a pausing
`pre-gate-stop` decision pauses the local run.

`LocalState` already places the personal paths: `state.extensions` is
`.git/agentmarshal/extensions/`, `state.switches_file` is
`.git/agentmarshal/switches.toml`. `journal/extensions.py`'s
`parse_extension_manifest_text` validates a manifest on text; the
directory-form helpers (`_manifest_directory_paths`,
`_require_existing_directory_file`) hold the schema-2 and file-presence
rules.

## Goals

- The clone's personal stages run through the same runner and the same
  `_run_stage` path as shared stages — no fork, no duplicate machinery.
- No grant, no journal authority, no footprint — the personal scope is
  the clone's own.
- Byte-identical output when no personal extension is present.
- Every existing transcript — `stage run`, `complete`, `doctor`,
  `status` — reads as it did.

## Non-Goals

- No file form for personal extensions — directory form only.
- No `extension add`/installer for the personal scope; the clone's
  author writes the directory.
- No `trust.toml` entries for personal extensions — the grant is not
  asked.
- No `record-ext` kinds from personal manifests.
- No personal `switch off` operational tasks — the personal switch is a
  local file, not a journal-governed operation.
- No per-stage `--skip-ext` or skip lists inside the manifest.

## Decisions

1. **Where the personal scope lives.** `.git/agentmarshal/extensions/`,
  reached only through `LocalState.extensions` — never computed as
  `.git/agentmarshal` by hand (ADR-0014). The name set is the
  directories and links there; `personal_extension_names` lists it.
2. **Directory form only, parsed the shared way.** A personal extension
  is `<name>/manifest.toml` plus the files the manifest names under
  `bin/` and `lock/`. `read_personal_manifest` reads the file, refuses a
  link at the directory or the manifest, checks the three forbidden
  top-level fields against the raw table first, then hands the text —
  prefixed with `footprint = []` and `documents = []` — to
  `parse_extension_manifest_text`, so every existing rule (schema,
  stages, isolation, records, wraps) applies unchanged. The
  directory-form schema-2 rule and the referenced-files check follow.
3. **Workstation only.** `run_stages` computes
  `ci = os.environ.get("CI") == "true"` once and plans no personal
  stage when it holds — personal discovery does not even enumerate the
  directory on CI, so nothing personal can print there.
4. **Materialize by copy, not by base.** Shared stages are materialized
  from the base tree; the personal directory is already in the
  filesystem, so `_prepare_personal_extension` copies it into the same
  per-stage temporary directory with `shutil.copytree(...,
  symlinks=True)`. The copy goes through `_run_stage`'s existing link
  and command checks, so a link inside the directory is refused the
  same way and the command runs from the copy — a stage cannot scribble
  on its own source.
5. **One pass, shared first.** Inside `run_stages`, after the shared
  loop, a second loop walks the personal plan — name-sorted, stages in
  manifest order — through the same per-stage body (switches, prepare,
  run, frames, result line, event, pause bookkeeping), parameterized by
  scope. Extension-level states (collision, disabled, skipped, refused
  manifest) print one line at the extension's sorted slot.
6. **The `(personal)` mark.** Every personal stage's result line is
  `<name>: <result> (personal)` — the mark is part of the result string,
  so pause entries, warnings and `complete`'s pause listing carry it
  unchanged. Personal `extension-event`s set `scope` to `personal`.
7. **Collision: shared wins, once.** A personal name in the base's
  shared name set gets one line —
  `<name>: not run (a shared extension of this name wins) (personal)` —
  and no stage of it is planned. The rule compares names, not stages or
  grant state: a switched-off or ungranted shared extension still wins
  its name.
8. **Forbidden fields refuse the extension, not the run.** A manifest
  declaring `footprint`, `documents` or `artifacts`, an unreadable
  manifest, a link — each prints `<name>: not run (<reason>) (personal)`
  on one line and plans no stage, like a shared prepare failure.
9. **The personal switches file.** `.git/agentmarshal/switches.toml`:
  `format = 1`, a `[switches]` table, per name a `state` of `on`/`off`
  and an optional `reason` under the same forgeable-text rule; `task`
  is not a personal field. `parse_personal_switches` is lenient about
  entries naming no live personal extension (a stale switch passes
  unread) and about keys beyond the shape. A missing file means all on;
  a malformed file is named on one line and all personal extensions
  stay on.
10. **`--skip-ext` is a run flag, not a switch.** `action="append"` on
    `stage run` and `complete`; it names a personal extension to skip
    for that invocation and prints `<name>: skipped for this run
    (personal)` at the extension's slot. It is validated against the
    base's shared names first — naming a shared extension refuses the
    run before any stage is planned — and passes to both of
    `complete`'s `run_stages` calls, so the skipped extension runs at
    no phase.
11. **disable/enable write the file, atomically.** `extension disable`
    writes `state = "off"` (plus `reason` when `--reason` is given)
    under `[switches.<name>]`; `extension enable` removes the entry.
    Both refuse a name no live personal extension declares, refuse a
    shared name with the operational-task line, and write through a
    temporary file and `os.replace` like `trust.toml`. `enable` on a
    not-disabled extension refuses. Neither touches the journal.
12. **Refusals name the rule once.** A shared name in any personal
    switch — flag or command — prints one line saying a shared
    extension is switched off only by an operational task
    (`extension switch off`); the commands write nothing, the run
    refuses before planning.
13. **Doctor adds lines, changes none.** After the shared extension
    lines come the personal ones — `extension <name>: personal scope,
    directory form, manifest schema <n>, stages: <modes>, ext kinds:
    <kinds>`, `disabled` appended when the switch is off — then
    `extension manifest <name> (personal)` checks, and
    `personal extensions: unavailable (<reason>)` /
    `personal switches: unavailable (<reason>)` when local state
    cannot be read. No line changes when there is no personal
    extension.
14. **No journal authority.** `record-ext` keeps reading only shared
    manifests; a kind declared only by a personal manifest is refused
    as undeclared. Personal stages write `extension-event`s only —
    `scope = "personal"` — and nothing to the journal.
15. **Stability.** Personal discovery adds nothing to `plan`; when the
    directory is absent or empty every existing line, note and check is
    byte-identical, `plan_empty` is unaffected, and both of `run_stages`'
    early returns keep their shape.
