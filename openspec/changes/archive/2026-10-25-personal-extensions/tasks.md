# Tasks: personal-extensions

## 1. Personal switches file

- [x] 1.1 `switches.py`: `PersonalSwitch` (`state`, optional `reason`);
      `personal_extension_names(directory)`; `parse_personal_switches`
      (format 1, `[switches]` table, lenient on unknown names/keys);
      `read_personal_switches(path, names)` on `LocalState.switches_file`.

## 2. Personal manifest read

- [x] 2.1 `extension_trust.py`: `read_personal_manifest(directory, name)`
      — link refusal at directory and manifest, forbidden `footprint` /
      `documents` / `artifacts` checked on the raw table, then
      `parse_extension_manifest_text` on the text with the empty arrays
      supplied; schema-2 and referenced-files rules from the directory
      form.

## 3. `run_stages` personal pass

- [x] 3.1 Move the `ci` computation up; plan personal entries on a
      workstation only — per name: collision line, disabled, skipped,
      manifest refusal, else its stage matching the phase modes.
- [x] 3.2 `_prepare_personal_extension` — copy the clone directory into
      the per-stage temporary directory (`symlinks=True`); reuse
      `_run_stage` unchanged.
- [x] 3.3 Parameterize the per-stage body by scope — shared first, then
      personal; `(personal)` mark on the result string; `scope` on the
      `extension-event`; extension-level lines at the name's sorted
      slot.
- [x] 3.4 `--skip-ext` on `stage run`; refuse a shared name on one
      operational-task line before planning; pass `skip` into
      `run_stages`.
- [x] 3.5 Keep both early returns byte-identical when no personal
      extension exists; `plan_empty` unchanged.

## 4. CLI

- [x] 4.1 `complete --skip-ext` — pass to both `run_stages` calls;
      refuse with `--findings`.
- [x] 4.2 `extension disable` / `extension enable` under the `extension`
      group — personal-name validation, shared-name refusal, atomic
      write of `switches.toml`, `--reason` on disable.

## 5. Doctor

- [x] 5.1 Personal lines after the shared ones (`personal scope`,
      `disabled` when switched off); `extension manifest <name>
      (personal)` checks; `personal extensions: unavailable` /
      `personal switches: unavailable` lines.

## 6. Tests

- [x] 6.1 One test per delta scenario — the exact scenario title in the
      docstring.
- [x] 6.2 Byte-identical transcripts where no personal extension
      exists.

## 7. Wrap-up

- [x] 7.1 `uv run agentmarshal validate`, `uv run pytest`,
      `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`.
- [x] 7.2 Archive with
      `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.15.0 archive personal-extensions --yes`.
