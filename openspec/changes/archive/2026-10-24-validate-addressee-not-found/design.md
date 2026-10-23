## Context

ADR-0013 decision 18 fixed the rule: `validate` checks the `ext`
envelope, and a `kind` no manifest declares draws a warning —
"addressee not found", not a refusal — because a record can outlive
the manifest that declared its kind. Reading the declared kinds makes
`validate` another reader of manifests, after `brief`, the gate and
`doctor` — where ADR-0010 decision 4 counted two.

The pieces this check composes all exist: `validate_journal` already
walks every task's validated records and prints `OK`/`FAIL` lines; the
`ext` envelope is validated on read, so a `kind` reaching the check is
always of the `<name>/<kind>@<version>` form; `read_extension_manifest`
(CR-152, CR-208) reads a manifest in either form with its symlink rules
and exposes `record_kinds` — the lookup `record-ext` (CR-212) makes for
the write side; `escape_for_display` renders a refused character as a
visible escape.

## Goals

- One `WARN` line per `ext` record whose `kind` no manifest declares,
  naming the task, the record id and the kind, worded "addressee not
  found".
- The manifests consulted are the shared extensions' in the journal
  repository's working tree, read in the file form
  (`.agentmarshal/extensions/<name>.toml`) or the directory form
  (`<name>/manifest.toml`).
- A manifest that cannot be read is named once on a `WARN` line and its
  kinds count as undeclared; the warning changes no verdict and no exit
  status.
- A journal with no `ext` records reads no manifest and prints byte for
  byte what it printed before.

## Non-Goals

- Refusing a record over its kind — the warning is not a refusal.
- Reading the payload — it is opaque to the core; the envelope alone is
  checked.
- Personal or user-scope manifests — they write no records (ADR-0013
  decision 9's scope table); only shared manifests are consulted.
- Protection beyond what the published decisions promise — see
  docs/threat-model.md.

## Decisions

- **The lookup is per `<name>`, as `record-ext` makes it.** The `<name>`
  segment of a kind names the extension, and a well-formed manifest can
  only declare kinds in its own namespace — `_parse_record_kinds`
  refuses a kind that does not name the manifest's extension — so
  consulting the `<name>`'s manifest answers "no manifest declares"
  exactly: no other manifest could declare the kind. The reader is
  `read_extension_manifest` on the journal repository's working tree —
  the same root `validate_journal` reads the journal from, so a sidecar
  reads its own tree — never a second reader and never an enumeration:
  a journal holding no `ext` record reads no manifest, and a manifest
  no record names is never opened.
- **The read is lazy and cached.** The declared kinds are resolved on
  first use and cached by name across tasks, so each manifest is read
  once however many records name the extension — the "one `WARN` line"
  an unreadable manifest owes falls out of the cache, not out of a
  separate dedup pass.
- **Missing and unreadable are reported differently.** A missing
  manifest (`ExtensionManifestMissing`) draws no line of its own —
  "addressee not found" is the report, the phrase the ADR chose for the
  extension that is not there. One that exists but cannot be read —
  malformed, a symlink, both forms at once — is named on a `WARN` line
  before the first addressee warning it causes, and its kinds count as
  undeclared.
- **`WARN` lines sit beside the task's own lines.** They print after
  the task's `OK`/`FAIL` lines, prefixed `WARN:`; the addressee line
  carries the task prefix the way `FAIL: <task>:` does, the
  manifest line carries none — it names the manifest, not a task.
  Nothing touches `passed`: a warning is not a refusal, and the
  verdict and the exit status are unchanged.
- **Every contributed value is escaped.** The record's id and kind, the
  manifest's name and the manifest error's own text pass through
  `escape_for_display` — as validate's other lines do with values they
  did not write (the artifact ref shown as `repr`); the manifest
  error is the one carrier that can hold a line-forging character.

## Risks

- [A second manifest reader or form rule drifting from the write
  side's] → there is none: `read_extension_manifest` is the one
  filesystem reader and the `<name>`-segment lookup is the one
  `record-ext` makes.
- [A warning quietly becoming a refusal] → WARN lines are appended to
  the report's lines only; `passed` is never touched, and a test pins
  the exit status.
- [Manifest reads where no record needs them] → the lookup is lazy and
  keyed on the records seen; a byte-for-byte test pins that a journal
  with no `ext` records reads no manifest and prints what it printed
  before.
- [A value forging a transcript line] → every record- and
  manifest-derived value is escaped; the manifest error — the one
  carrier able to hold a forging character — is asserted escaped in a
  test.
