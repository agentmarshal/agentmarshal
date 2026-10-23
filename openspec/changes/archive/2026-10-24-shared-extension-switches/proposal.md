## Why

ADR-0013 decision 16 puts a shared extension's switch apart from its
manifest: only an operational CR can switch it off — neither a flag nor
a local setting. Decision 17 gives the operational CR its shape — the
diff touches only `.agentmarshal/switches.toml` (name → on/off,
reason) — and has `status` and `doctor` say "switched off since CR
so-and-so, reason". Decision 6 reads the switches from the base commit
with the rest of the trusted inputs; decision 7's no-silence rule makes
a switched-off extension still get a result line. ADR-0022 section 7
gives the file's shape, ADR-0014's map places it, and CR-211 runs the
stages the switch now governs. Today nothing reads the file: an
operational CR could write it and nothing would change.

## What Changes

- A new `switches.py` parses `.agentmarshal/switches.toml` fail-closed:
  `format = 1`, and per extension name a `state` (`on` or `off`), the
  operational CR that set it (`task`, `CR-<n>`) and — required when
  `off`, refused when `on` — a `reason` of at most 1000 characters
  passing the forgeable-text rule. A file that is not UTF-8 TOML, a
  missing or unknown `format`, an entry that is not a table, an entry
  naming no shared extension, or a field outside its shape is refused
  naming the file and, where one exists, the entry.
- `stage run` reads the switches from the merge base's tree — never
  the candidate's and never the working tree's — parsed against every
  shared extension name the base enumerates, both forms. A stage of a
  switched-off extension prints `switched off (<task>, <reason>)` as
  its one result line and does not run: no materialization, no grant
  check, no pause for `pre-gate-stop`, no warning for `pre-gate-warn`;
  its `extension-event` carries decision `switched-off`. A switches
  file the parse refuses is reported on one line and no stage of an
  extension it names runs — each is `not run` — and a file whose
  entries cannot be read at all leaves every stage `not run`.
- `doctor`'s extensions section reads the file from the working tree
  and shows each switched-off shared extension — `switched off since
  <task> (<reason>)` — on its line, file form and directory form
  alike. A project without the file shows nothing new; a file the
  parse refuses is named on one `switches: unavailable` line, never a
  check failure.
- Every value the file carries is escaped on display.

## Capabilities

- modified: `extension-stages`

## Impact

`src/agentmarshal/switches.py` is new: one parse function and the
working-tree reader, in the shape `extension_trust.py`'s `trust.toml`
reader established. `src/agentmarshal/stages.py` enumerates the base's
extension names in both forms (file-form names validate switch entries
too), reads the switches blob at the merge base, and turns a
switched-off stage into its result line before materialization would
start. `src/agentmarshal/doctor.py` reads the working-tree file inside
its extensions section. The gate is unchanged — the operational lane
is a later task — and no other command changes. Out of scope by the
contract's own staging: opening the operational CR
(`extension switch off`), personal switches, `--skip-ext`, and the
`status` half of decision 17's showing.
