## Context

ADR-0013 decision 17 ends: "`status` and `doctor` show 'switched off
since CR so-and-so, reason'". CR-217 implemented the `doctor` half —
`switched off since <task> (<reason>)` on the extension's own line —
and this change implements the `status` half. ADR-0014 decision 13
already puts `status`'s places-of-things lines on stderr: stdout is a
documented parser contract, so the new lines join the stderr report
where the journal, the process log and the local state print.

The pieces this change wires together already exist:
`switches.read_switches` is the working-tree reader `doctor` calls;
`switches.shared_extension_names` is `doctor`'s enumeration rule moved
into one place by CR-220 — a `<name>.toml` entry the file form, a
`<name>/` entry the directory form, a link kept under the name it
carries, a name in more than one form enumerated once, a managed path
that is no directory enumerating no names;
`extension_trust._managed_directory` resolves the extensions directory
with its symlink refusals; and `escape_for_display` renders every
forgeable character as a visible escape.

## Goals

- Whoever reads `status` sees that a shared check is switched off, by
  which task and why, without a second command.
- The names "the shared extensions the working tree declares" are
  enumerated by one function — `doctor` moves onto
  `shared_extension_names`, and `status`'s switches read checks the
  file's entries against it.
- `status`'s stdout — the parser contract — is unchanged byte for
  byte, in every case.

## Non-Goals

- Personal switches — a later task, as the contract declares.
- Any change to `status`'s stdout, or to any other command.
- Protection beyond what the published decisions promise —
  `docs/threat-model.md` already records the bounds.

## Decisions

- **The lines print where the paths print.** In `_run_status` the new
  lines go on stderr right after the `print_paths` call, in both the
  listing and the single-task view, before anything that can return
  early — an empty journal's `No tasks.` and a task lookup's refusal
  both come after the paths, and the switched-off lines are owed in
  every case the paths printed.
- **The read is `doctor`'s.** Same file — `placement.project_root /
  SWITCHES_RELPATH`, the working tree's file, the journal repository's
  own in a sidecar — through the same `read_switches`, parsed against
  `shared_extension_names(_managed_directory(project_root))`. The
  refusal goes through the same wording `doctor` reports it with —
  `switches: unavailable (<reason>)` on one stderr line — and is a
  report, never a failure: the exit status and stdout are unchanged.
- **The line names the extension first.** Where `doctor` carries the
  switch inside the extension's own line, `status` has no per-extension
  lines to join — each switched-off extension gets a line of its own:
  `switched off: <name> since <task> (<reason>)`, in the enumeration's
  sorted order, escaped whole the way `doctor` escapes its lines.
- **`doctor`'s `_extension_names` is removed.** Both enumeration sites
  take `sorted(shared_extension_names(managed))` — the function checks
  `is_dir` itself, so the sites' `managed.is_dir()` guard folds in —
  keeping the sorted list shape the loops and the byte-for-byte output
  the existing tests pin.
