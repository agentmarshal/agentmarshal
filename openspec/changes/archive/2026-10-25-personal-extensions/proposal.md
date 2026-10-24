# Change: personal-extensions

## Why

ADR-0013 gives the process two extension scopes. The shared scope — an
extension committed at `.agentmarshal/extensions/`, read at the base,
granted once — shipped with `stage run` and `complete`. The personal scope
was decided with it and deferred: a stage the clone's author runs for
themselves, from the clone, with no grant and no journal authority
(decisions 9–11, 16; ADR-0014 places it at
`.git/agentmarshal/extensions/`). This change adds that scope.

## What Changes

- `stage run` — and `complete` through the shared runner — also run the
  clone's personal extensions' declared stages, on a workstation only.
  A personal extension is a directory `<name>/` under the clone's
  `.git/agentmarshal/extensions/` carrying `manifest.toml`; the manifest
  is read from that directory, never the base, and the stage runs under
  the same `_run_stage` path as a shared stage.
- Personal stages need no grant. Their result lines carry a `(personal)`
  mark; a pausing `pre-gate-stop` personal stage pauses the local run the
  same way, marked, and `complete` reports the pause or the already-merged
  warning exactly as for a shared stage.
- A personal manifest carries no `footprint`, `documents` or `artifacts`
  — a personal extension has no footprint in the repository and never
  writes a record. One that declares any is refused.
- A personal extension named like a shared extension is not run — the
  shared one wins — and is named on one line.
- Personal switches: `stage run --skip-ext <name>` and
  `complete --skip-ext <name>` skip a personal extension for the run;
  `extension disable <name>` and `extension enable <name>` write and
  clear `state = "off"` entries in the clone's
  `.git/agentmarshal/switches.toml`. A shared extension is never named
  in a personal switch — it is switched off only by an operational task.
- `doctor` lists personal extensions with the `personal` scope and runs
  a manifest check per extension.
- In CI no personal stage is planned and nothing personal is printed; a
  clone with no personal extension gets exactly the transcript it gets
  today.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `extension-stages` — the shared scope gains the personal one beside it,
  through the same runner.

## Impact

- `src/agentmarshal/stages.py` — personal discovery, plan and run inside
  `run_stages`; the `(personal)` mark; the collision, refusal and switch
  lines; `--skip-ext` on the `stage run` parser.
- `src/agentmarshal/switches.py` — the personal switches file read.
- `src/agentmarshal/extension_trust.py` — `extension disable` and
  `extension enable`; the personal manifest read.
- `src/agentmarshal/doctor.py` — personal listing and checks.
- `src/agentmarshal/cli.py` — `--skip-ext` on `complete`.
- `tests/` — one test per scenario.
