## Why

ADR-0013 decision 17: `status` and `doctor` show "switched off since CR
so-and-so, reason". CR-217 gave `doctor` that line; `status` has none —
whoever reads `status` cannot see that a shared check is switched off, by
which task or why, without a second command. CR-220 added
`switches.shared_extension_names` with exactly `doctor`'s enumeration
rule and left `doctor` moving onto it as a follow-up, so the rule lives
in one place.

## What Changes

- `status` — the listing and the view of one task alike — prints on
  stderr, right after the lines naming where the journal, the process
  log and the local state live, one line per shared extension the
  working tree's `switches.toml` switches off:
  `switched off: <name> since <task> (<reason>)`, every value escaped
  for display. The lines are owed in every case where the paths
  printed — an empty journal's `No tasks.` and a task lookup's refusal
  alike. stdout is unchanged byte for byte.
- The file is the one `doctor` reads — the working tree's
  `.agentmarshal/switches.toml` through `read_switches`, parsed against
  the names `shared_extension_names` enumerates for
  `.agentmarshal/extensions/`. A file the parse refuses is named on one
  `switches: unavailable (<reason>)` line and changes neither the exit
  status nor stdout; a project without the file, or with nothing
  switched off, prints nothing new.
- `doctor` enumerates the working tree's shared extension names through
  `switches.shared_extension_names`; its own `_extension_names` is
  removed. `doctor`'s output is unchanged byte for byte.

## Capabilities

- modified: `extension-stages`

## Impact

`src/agentmarshal/cli.py`'s `_run_status` gains the switched-off lines
beside its `print_paths` call; `src/agentmarshal/doctor.py` drops
`_extension_names` for the shared function at both enumeration sites.
No other command changes; `status`'s stdout — a documented parser
contract — is untouched. Personal switches and any protection beyond
the published decisions stay out of scope, as the contract's non-goals
declare.
