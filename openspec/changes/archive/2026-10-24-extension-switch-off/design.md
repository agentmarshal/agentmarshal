## Context

ADR-0013 section E pairs two decisions: 16 — a shared extension is
switched off only by an operational CR, and the switches live apart
from the manifest and the grants — and 17 — the operational CR touches
only `.agentmarshal/switches.toml` and its own task's records, needs no
review, carries a mandatory reason, and is opened with one command,
`agentmarshal extension switch off <name> --reason "…"`. CR-217 built
the file's parser (`switches.py`'s `parse_switches`, fail-closed, and
`read_switches` for the working tree) and its two readers; CR-219 in
parallel builds the gate lane that admits the diff. This change is the
writer — the command that produces the lane's input in one step.

The pieces already exist: `journal/open_task.py`'s `open_task` opens a
task from a supplied contract (`contract_file=`), retargeting its
header `id` to the assigned task id and pinning the contract hash on
the `opened` record; `journal/extensions.py`'s `_validate_name` is the
extension-name rule every extension command applies;
`extension_trust.py` holds the working tree's managed directory
(`_managed_directory`, with its link refusals) and the TOML
basic-string writer (`_toml_string`) `trust.toml` is dumped with;
`journal/display.py`'s `escape_for_display` is the display half of the
forgeable-text rule; and `cli.py`'s `_placement` is the pattern every
command resolves its journal placement with.

## Goals

- One command produces the whole operational change — the opened task
  and the switch written for it — for a developer to commit and send
  through the gate.
- The task is opened by the journal's own transaction and the file by a
  surgical rewrite the parser itself verifies — nothing hand-rolled, no
  TOML writer added.
- Every check that can fail before the task exists fails before it is
  opened, so an early refusal leaves no trace: no task, no file.

## Non-Goals

- `switch on` — switching back on is an edit of the file in an
  operational task; a command for it is a later task.
- Personal switches (`.git/agentmarshal/switches.toml`),
  `extension disable`, `--skip-ext` — ADR-0013 decision 16's personal
  side is later work.
- The gate's operational lane and `accept --operational`'s reading of
  it — CR-219 and CR-218 in parallel.
- Committing, pushing or opening a pull request — the command's output
  is the working-tree change, nothing more.

## Decisions

- **The contract is generated and opened through `contract_file=`.**
  `open_task` is the journal's only opening transaction; the command
  writes the generated contract to a temporary file and passes it, so
  the `opened` record pins the contract's hash the way every task's
  does. The header declares `id = "CR-000"` — a placeholder
  `open_task`'s own retargeting replaces with the assigned id — and the
  replaced-id notice prints on stderr the way `open` prints it. The
  title names the extension; the scope is exactly
  `[".agentmarshal/switches.toml"]` — the bound ADR-0013 decision 17
  gives the lane; `acceptance` says the extension is switched off with
  the reason, and `decisions` names ADR-0013. `scope_warnings` is not
  consulted: the generated scope is the one entry the lane admits, and
  the file may legitimately not exist yet — the warning exists for
  scopes a human writes.
- **Name, reason and the existing file are checked before the task is
  opened.** The name passes `_validate_name` and must then be a shared
  extension the working tree declares — the enumeration the manifest
  readers share: a `<name>.toml` entry or a `<name>/` directory under
  `.agentmarshal/extensions/`, a link kept under the name it carries.
  The reason is checked against the parser's own rule — non-empty, at
  most `REASON_CHAR_LIMIT` characters, `reject_control_characters` — so
  the file the command writes can never contain a reason the parser
  refuses. The existing `.agentmarshal/switches.toml` — a link at its
  path refused outright — is parsed against the declared names: a file
  the parse refuses is refused naming it, and an entry already `off`
  is refused naming the task that switched it off. The rewrite itself
  is verified at the same point — the check the next decision gives —
  and only then is the task opened: every earlier refusal writes
  nothing.
- **The rewrite is textual, not a serialization.** There is no TOML
  writer in the dependencies and none is added, so the existing text is
  kept and only what the switch needs changes. An `on` entry's
  `[switches.<name>]` table — the header line in every spelling TOML
  allows for the two keys, whitespace and trailing comment included —
  has its key/value lines replaced; the header line and whatever trails
  the table's last content line — blank lines, comments — stay. Any
  other extension gains a `[switches.<name>]` table appended after the
  file's existing content; a missing file is created as `format = 1`, a
  `[switches]` table and the entry. `reason` is quoted by
  `_toml_string` — every character a TOML basic string must escape is
  escaped — and `task` carries the opened task's id.
- **The new text is verified before the task is opened and again
  before the file is replaced.** A line scanner cannot tell a table
  header from a `[`-led line inside a multi-line value, so the
  rewritten text is trusted only as far as TOML itself proves it. It
  is built first under a placeholder task id — `CR-0`, a `CR-<n>` of
  the valid form the allocator never assigns — and accepted only where
  `tomllib.loads(new)` equals `tomllib.loads(old)` — the empty
  document where the file is missing — everywhere except the one
  `switches` entry, which must be exactly the off entry, and where
  `parse_switches` reads the entry back as `off` with the placeholder
  task and the reason. Any mismatch — a mis-detected span, an `on`
  entry carried in a form with no table header to replace, anything —
  refuses before the task is opened, on one line naming the file and
  saying the entry must be switched off by editing the file in an
  operational task, writing nothing. After the open, only the `task`
  value's string changes to the real id and the same check runs again
  before the replace; a failure there is reported like any other
  post-open failure.
- **The replace is atomic and lands beside the file.** A temporary
  file is created in `.agentmarshal/` — the switches file's own
  directory, the same-directory rule `_write_grants` follows — written,
  then `os.replace`d over the target; a failure anywhere unlinks the
  staging file and leaves the previous file whole.
- **A post-open failure names the task once.** If the task opened but
  the file could not be written — the staging file, the parse-back, the
  rename — the command says so on one line naming the opened task and
  exits non-zero. The task stands in the journal: abandoning it is the
  record for giving it up, not something the command decides. The
  command prints the contract's and the record's paths as `open` does,
  then the switches file's path, and commits nothing.
- **A sidecar opens no operational task.** The placement resolves by
  `cli.py`'s `_placement` pattern — without `require_host`, since the
  command never touches the host — and a sidecar refuses on one line:
  operational tasks are not available in a sidecar. An operational CR's
  force is the gate lane that admits its diff, and the sidecar gate
  advises and decides no merge — the refusal is before every check
  that depends on the working tree, and nothing is written.
- **Registration nests `switch` under `extension`.** `extension_trust`'s
  `register` adds a `switch` group with its own subparsers — `off
  <name> --reason <text>` — and `run` dispatches `switch` to
  `switch_off.run`, imported where it is dispatched: `switch_off`
  borrows `_managed_directory` and `_toml_string` from
  `extension_trust`, so a top-level import in either direction would be
  circular. `trust`, `untrust` and `list` keep their code paths
  untouched.
- **Every value shown is escaped on display.** The file's own values —
  a quoted entry name in a parse refusal, the task an already-off entry
  names — and every path and error the command prints pass
  `escape_for_display`, the way the other extension surfaces do — the
  success lines included: the contract's, the record's and the
  switches file's paths.
