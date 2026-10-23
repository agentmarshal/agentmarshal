## Context

ADR-0013 decision 14 makes a local grant cover the hash of a shared
extension's whole directory; decision 15 bounds what that protects
against. ADR-0014's map places `trust.toml` in the clone's local state —
`.git/agentmarshal/trust.toml` — which `localstate.py` already resolves as
`LocalState.trust_file` beside `log/`, `extensions/`, `deps/` and the
switch and plan files. ADR-0022 section 7 fixes the file's shape — a name
to the directory hash granted, who granted it and when — and lists
`trust-changed` among the process log's event kinds; `process_log.py`'s
`open_writer`/`write_event` already write such events. The directory-form
extension itself — `.agentmarshal/extensions/<name>/` against the file
form `<name>.toml` — is what `journal/extensions.py` reads and its
`_validate_name` validates a name for; `resolve_recorded_by` in
`journal/actors.py` is how every writer resolves the acting identity. The
command-group shape — a module's own `register(subparsers)` and
`run(args, stderr)` — is what `steps.py` established.

## Goals

- A developer approves a shared extension's exact contents on one clone,
  withdraws the approval, and sees which extensions changed since.
- The grant names its file: a symlink or a non-regular file inside the
  directory, a file-form extension, a missing directory — each refusal
  says what it found.
- `trust.toml` is fail-closed on read and atomic on write, and every
  grant and removal leaves one `trust-changed` event in the process log.
- Nothing runs an extension, nothing writes the journal, and `list`
  writes nothing at all.

## Non-Goals

- The check before each run and running extensions (ADR-0013 decision 14's
  second half) — later tasks; this task only keeps the grants.
- Personal and user-scope extensions, `doctor`'s grant line, switches.
- Defence against a process with the user's rights (ADR-0013 decision
  15): no locking, no TOCTOU machinery, no ownership checks. The same-user
  threat is out of scope by decision, not by oversight.
- Parsing or validating `manifest.toml`: the grant approves directory
  contents, not manifest validity — the manifest reader judges that when
  an extension is invoked.

## Decisions

- **The grant is over every regular file, keyed by relative path.**
  `trust` walks `.agentmarshal/extensions/<name>/` entry by entry in
  sorted order: a symlink — to a file, to a directory, dangling or not —
  refuses the grant naming its relative path, before existence or type is
  weighed; a regular file is hashed (sha256 of its contents) under its
  `/`-joined path relative to the directory; a directory recurses;
  anything else — a fifo, a socket, a device — refuses the grant naming
  it. The walk is manual rather than `rglob`, because on every Python
  this project supports a recursive glob follows symlinked directories —
  exactly the escape the refusal exists to stop. Sorted traversal makes
  the first refusal deterministic. The extension's own directory is held
  to the same rule the manifest reader applies: a symlinked `<name>` is
  refused as a link, and so is a symlink at `.agentmarshal` or at
  `extensions/` — checked lexically after the project root is resolved,
  so an ancestor link in the operator's own path is not the hazard.
- **The directory hash is one hash over the sorted path–hash list.** For
  each file in relative-path order the hasher takes the path's UTF-8
  bytes, a NUL byte, the file's lowercase hex sha256, another NUL byte.
  NUL cannot occur in a path, so the framing is unambiguous; sorting
  makes the value depend on contents alone — same files, same hash, in
  whatever order the filesystem hands them back. It is deliberately not
  the hash of the manifest alone (ADR-0013's refused alternative) and not
  a Merkle tree — the flat list is what the grant file itself stores, so
  the per-file comparison `list` needs and the directory hash come from
  one pass.
- **`trust.toml` is `format = 1` with a `grants` table.** Each grant is
  `[grants.<name>]` carrying `directory_hash`, `granted_by`,
  `granted_by_source`, `granted_at` (UTC ISO-8601) and a
  `[grants.<name>.files]` sub-table of relative path to file hash.
  `granted_by`/`granted_by_source` are the pair `resolve_recorded_by`
  returns — actor plus how it resolved — the same provenance shape the
  record family keeps. The format version lives inside the file
  (ADR-0022 section 7's rule for local formats): `format` missing or not
  `1`, a file that does not parse, and a grant missing a field or
  carrying the wrong type are each refused naming the file — malformed or
  unknown-format reads never produce a half-trusted state for any
  subcommand. A missing `trust.toml` is not malformed — it reads as no
  grants. The file is written by a minimal serializer for this one fixed
  shape — quoted keys and strings escaped for `"`, `\` and control
  characters — read back through `tomllib`; no new dependency.
- **Writes are a temporary file renamed into place.** `trust.toml` is
  written to a `mkstemp` file in the local state root and `os.replace`d
  over the old name, so a reader never sees a half-written file and a
  failed write leaves the previous file whole. The local state root is
  created through `LocalState.ensure_directory` — the contained creation
  call — before the staging file is opened. There is no fsync and no
  lock: the process log sets the durability bar for local state, and
  decision 15 assigns the same-user threat no defence.
- **The grant, not the file, decides `untrust`.** `untrust` needs no
  extension directory at all — a grant outliving its extension is how the
  file gets cleaned — and no recorder identity, since nothing is
  recorded; it refuses only a name with no grant, naming it. `trust`
  refuses when `resolve_recorded_by` finds nothing — a grant naming
  nobody attests nothing — with the same message `agree` gives.
- **`trust-changed` carries `extension`, `action` and `directory_hash`.**
  `granted` carries the new directory hash, `removed` the hash the
  removed grant held — the event records what changed hands, so a
  removal's hash is the stored one even when the directory is gone or
  changed since. `actor` rides along when an identity resolves (for
  `trust` it always has, the command having refused otherwise). The state
  change is written first, the event second: a failed event reports that
  the grant landed but its event did not, rather than logging a change
  that never happened. A refused command appends no event.
- **`list` compares per file, not per directory hash.** The state is
  derived from the stored per-file hashes against a fresh walk: the
  first path in sorted order that was removed, added or whose hash
  changed is named — `changed after approval: <path> (<kind>)` — which is
  exactly the information the run-time refusal of decision 14 will owe.
  A file-set that still matches is `granted` whatever the stored
  directory hash says; the per-file record is the substance.
- **Ambiguity and form are decided once, in one place.** A `<name>.toml`
  and a `<name>/` directory for one name refuse `trust` naming both
  paths, the reader's own rule; `<name>.toml` alone is a file-form
  extension with no directory to grant; `<name>` present but not a
  directory is named; neither form is a missing extension. `list`
  enumerates real directories under `.agentmarshal/extensions/` — a
  symlinked entry is named rather than hashed through — and file-form
  entries are not extensions it lists.
- **The group is `extension`, the module is `extension_trust`.**
  `register` adds `extension` with `trust`, `untrust` and `list`
  subcommands under `dest="extension_command"`; `run` dispatches — the
  shape `steps.py` and `outbox.py` already established, so the command
  surface stays one register-call wide in `cli.py`.

## Risks

- [A file changes between hashing and the grant write] → accepted:
  decision 15 bounds this to accidental change, and the pre-run check —
  a later task — recomputes anyway.
- [A grant for a since-deleted extension lingers] → `untrust` removes it;
  `list` reports only extensions present, so a stale grant hides nothing.
- [A hand-edited `trust.toml`] → the read is fail-closed on structure and
  format; a same-user editor with intent is already outside the model.
- [An empty extension directory] → grants over no files: harmless — the
  directory hash of an empty list is still one value, and nothing runs.
- [The empty writer file a failed `trust-changed` leaves] → the process
  log's one-file-per-writer design already tolerates empty files; the
  failure is reported on stderr.
