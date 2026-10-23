## Context

ADR-0013 section E is short and sharp: switches live apart from the
manifest (decision 16), a shared extension is switched off only by an
operational CR whose diff touches only `.agentmarshal/switches.toml`
and whose reason is mandatory (decision 17), the switches are read
from the base like every other trusted input (decision 6), and a
switched-off extension still gets a result line (decision 7's "no
silence" — `switched off (by whom and why)`). ADR-0022 section 7 fixes
the file among the local formats — "a name to on/off and the reason" —
and ADR-0014's map places it committed, next to `project.json`. The
threat model names the file as the one configuration that changes
without review — "easy, but not silent".

The pieces this change wires together already exist:
`journal/gate.py`'s `_tree_entry` and `_run_git_bytes` read a blob
from a base tree the way `_manifest_from_tree` does;
`extension_trust.py`'s `_read_grants` is the established shape for a
fail-closed TOML file with a `format` version; `journal/contracts.py`'s
`reject_control_characters` applies the forgeable-text rule the record
side shares; `journal/display.py`'s `escape_for_display` is the
display half of that rule; and `stages.py` already turns any
per-stage refusal into a `not run (<reason>)` result line, an
`extension-event`, and the pause/warn accounting.

## Goals

- A shared extension an operational CR switched off is visibly not run
  everywhere it would have run — each of its stages gets
  `switched off (<task>, <reason>)` and nothing executes.
- The switch file is read where the ADR puts it: the base commit for
  `stage run`, the working tree for `doctor` — a candidate can neither
  switch a check off for its own run nor switch one back on.
- The file fails closed: a malformed file, an unknown format, or an
  entry naming no shared extension refuses naming the file and the
  entry — and `stage run` runs no stage of an extension a refused
  file names.

## Non-Goals

- Opening the operational CR (`agentmarshal extension switch off`),
  the gate's operational lane, and operator acceptance of one — the
  file is read here, never written.
- Personal switches (`.git/agentmarshal/switches.toml`),
  `--skip-ext`, `extension disable/enable` — personal extensions are
  a later task.
- `status`'s half of decision 17's "status and doctor show" — the
  command's surface is untouched here.
- Protection beyond the published decisions — `docs/threat-model.md`
  already records that a symlink at `.agentmarshal/switches.toml`
  has no published refusal; this change adds none.

## Decisions

- **The file's shape mirrors `trust.toml`'s.** `format = 1` at the top,
  then `[switches.<name>]` tables — a semantic table name like
  `grants.<name>` — each carrying `state`, `task` and `reason`.
  `state` is `"on"` or `"off"`; `task` is the operational CR that set
  the switch, `CR-<n>`, required on every entry; `reason` is required
  exactly when `state` is `"off"` — an `on` entry carrying one is
  refused, since a reason for being on is ambiguous noise — bounded at
  the ADR-0022 section 8 figure of 1000 characters and held to the
  forgeable-text rule. Unrecognised keys inside an entry pass unread,
  the same newer-format tolerance grants entries get.
- **One function parses; each caller supplies the names.** `parse_switches`
  takes the file's bytes, a source string for its refusals, and the
  shared extension names the caller knows — the criterion's "an entry
  naming no shared extension" is the caller's set: for `stage run`
  every name the base's `.agentmarshal/extensions/` enumerates
  (directory form and `<name>.toml` alike — a file-form extension is
  a shared extension with no stages), for `doctor` the working-tree
  names. A missing file is not a refusal: every extension is on.
- **`SwitchesError` carries the entry names the file declares.**
  Where the TOML parsed far enough to enumerate the `switches`
  table's keys, the error's `names` is that set; where it did not —
  broken TOML, a non-table `switches`, an entry at the file's path
  that is not a blob — `names` is `None`, meaning the file could have
  named anything. `stage run` blocks the stages of exactly the named
  extensions — an extension the file does not name was never touched
  by it and runs — and blocks every stage when the names cannot be
  read, because an unreadable file cannot vouch for any extension
  being on. The refusal is reported once, on one stderr line naming
  the file and, where the parse reached one, the entry.
- **A switched-off stage is a decision of its own, not a failure.**
  `switched-off` joins the `_StageDecision` vocabulary: the result
  line is `<name>: switched off (<task>, <reason>)` — decision 7's
  "(by whom and why)" — the `extension-event` records the same
  decision and reason, and the stage is excluded from both the
  `pre-gate-stop` pause and the `pre-gate-warn` warning. The check is
  skipped before materialization or the grant check begins: nothing
  executes, nothing is trusted beyond the file itself. The switched-off
  line is therefore owed even where the workstation's `trust.toml`
  cannot be read — the stage was never going to be grant-checked:
  that refusal still fails the command on its one line, but only after
  every switched-off outcome in the plan has been reported; no stage
  that would be grant-checked runs, and the exit is 1. This is the
  reading of "a switched-off pre-gate-stop extension does not pause":
  an operational CR silences the check it names — the file's
  visibility, not the pause, is the audit.
- **A refused switches file is named even where nothing would run.**
  The base read happens before the empty-plan return, so a file the
  parse refuses is reported on its one stderr line even when the
  requested phase declares no stage — then the
  `no shared extension declares a <phase> stage` line and exit 0,
  unchanged: nothing was blocked, because nothing would have run. The
  trust file keeps its place after the empty-plan return — grants are
  consulted only where a stage exists to check.
- **`doctor` shows the switch on the extension's own line.**
  `switched off since <task> (<reason>)` joins the line's parts after
  the grant state — the report's shape stays one line per extension —
  for the file form as for the directory form, and even on the line
  that reports an unreadable manifest. A file the parse refuses does
  not fail a check: the section names `switches: unavailable` with
  the reason, the way an unreadable grants file marks the grant
  position unavailable.
- **Values from the file are escaped wherever they print.** The
  result line, the doctor line and every refusal pass
  `escape_for_display`; the one value that can still carry a
  forgeable character to display is an entry name a refusal quotes —
  the parse refuses forgeable `reason` text before it can render.
