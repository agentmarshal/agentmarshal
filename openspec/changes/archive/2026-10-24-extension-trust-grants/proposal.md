## Why

ADR-0013 decision 14 gives a shared extension a local run grant: a
developer approves the hash of the extension's whole directory — the
manifest, `bin/`, the lock — and a shared extension with a command later
runs on a workstation only under a valid grant. ADR-0014's map of places
puts the grants file, `trust.toml`, in the clone's local state;
ADR-0022 section 7 fixes its shape — a name to the directory hash granted,
who granted it and when — and names the `trust-changed` process-log event.
The file also keeps each file's own hash, so a refusal can name the file
that changed. Nothing keeps these grants today: there is no `extension`
command group, no trust file, no event.

## What Changes

A new `extension` command group, registered from its own module the way the
`step` group is, keeps the grants:

- `extension trust <name>` hashes every regular file under
  `.agentmarshal/extensions/<name>/` — sha256 by relative path, sorted —
  and one directory hash over that sorted list, and records the grant in
  `trust.toml` (`format = 1`, keyed by name: the directory hash, the
  per-file hashes, who granted it and when). A symbolic link or a
  non-regular file inside the directory refuses the grant naming it; a
  file-form extension or a missing directory refuses naming why.
- `extension untrust <name>` removes the grant, refusing when none is
  recorded.
- `extension list` recomputes the hashes and prints each shared extension
  in directory form with its state — granted, not granted, or changed
  after approval naming the first changed, added or removed file by sorted
  path. It never writes.

`trust.toml` is written atomically — a temporary file renamed into place —
and a malformed or unknown-format file refuses every subcommand naming the
file. Each grant and each removal appends one `trust-changed` event to the
process log carrying the extension name, the action and the directory
hash. No command runs an extension; nothing is written to the journal.

## Capabilities

- new: `extension-trust`

## Impact

The check before each run of ADR-0013 decision 14 gets the grants it will
read: `trust.toml` under `.git/agentmarshal/`, keyed by extension name,
holding the directory hash and each file's hash so the refusal can name
`changed after approval: <file>`. The bound of ADR-0013 decision 15 stands
— the file is local state and does not resist a process running with the
user's rights; nothing locks it or checks ownership. Running extensions
and the check itself are later tasks.
