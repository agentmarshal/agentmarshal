## Context

ADR-0013 extends ADR-0007's operator acceptance twice: decision 5 lets
an acceptance stand over an extension pause — which raises no review
finding — and decision 17 lets an adopter require an acceptance for an
operational CR — which carries no review at all. ADR-0022 section 2
names the record fields: `accepted_pause: {extension}` and
`operational: true`, each bound by `accepted_commit`. CR-173 landed the
record model, the readers and `create_acceptance_record`'s
`accepted_pause=` and `operational=` parameters; the operator-facing
write is what remains.

The pieces the command composes all exist: `accept_findings`
(acceptance.py) is the trusted path that loads the task through
`load_task_for_record` — the lifecycle admission every record writer
gets — and writes through `write_record`; `read_extension_manifest`
(CR-152, CR-208) reads a shared extension's manifest from a working
tree in the file form or the directory form with its symlink rules;
and `record-ext` (CR-212) resolves `--commit` to the full 40-hex id
with `git rev-parse --verify <rev>^{commit}` in the journal's
repository — the repository that holds the journal in either
placement, so a sidecar records against its own commits.

## Goals

- `accept --task <id> --commit <rev> --pause <extension> --by <party>
  --reason <text>` writes an acceptance carrying `accepted_pause`
  naming `<extension>`, bound by `accepted_commit` to the resolved
  commit, no `findings`; `<extension>` must name a shared extension
  the working tree declares.
- `accept --task <id> --commit <rev> --operational --by <party>
  --reason <text>` writes an acceptance carrying `operational: true`
  bound the same way; the task needs no review.
- The three forms are mutually exclusive and exactly one is required;
  refusals name the flags and write nothing.
- Acceptance over findings is unchanged, and no other command changes.

## Non-Goals

- The gate or the stage runner reading these acceptances — later
  tasks; a pause or operational acceptance still satisfies no gate
  lane (the readers' spec already pins that).
- Opening an operational CR (`extension switch off`) or pausing a
  process — later tasks; this change only records the decision.
- The findings form's own rules — the latest non-approving review of
  the exact binding, every blocking finding named — untouched.

## Decisions

- **The form flags are a second mutually exclusive group.** `--pause`
  takes the extension name, `--operational` is a flag; argparse's
  group makes them refuse each other naming both. The existing
  binding group — `--commit` xor `--accepted-finding`, required —
  is untouched: the findings form selects itself by naming neither
  new flag, exactly as today, and its parse-time refusals keep their
  shape. With a new form named, `--accepted-finding` and `--finding`
  are refused in `_run_accept` before placement resolves — a refusal
  that names the flags and can never write — and `--commit` is the
  one binding the group could have supplied.
- **The commit resolves in the journal's repository.** `record-ext`'s
  `rev-parse --verify <rev>^{commit}` pattern, replicated in
  `acceptance.py` the way `record_ext.py` replicates it: what resolves
  is the full 40-hex id the record binds, what does not is refused
  naming the reference — a short id, `HEAD` or a branch all land on
  the same `accepted_commit`. The findings form's `--commit` keeps
  comparing verbatim against `reviewed_commit`; only the new forms
  resolve.
- **The extension is checked against the working tree's manifests.**
  `read_extension_manifest(placement.project_root, <name>)` — the
  journal repository's working tree, the same root `record-ext` reads
  kinds from — answers "a shared extension declares this name" in
  either form with its symlink rules; `ExtensionManifestMissing` and a
  malformed manifest both land the refusal naming the extension, the
  manifest's own message saying which. The record's own name rule
  (`accepted_pause.extension` is one path component, forgeable text
  refused) still applies at write — a name the manifest layer refused
  never reaches it, and the two cannot drift: the manifest check runs
  `_validate_name` first.
- **No review is consulted.** `accept_findings` derives its findings
  from the task's latest non-approving review of the exact binding;
  the new path calls `load_task_for_record` for the lifecycle
  admission alone. A pause raises no review finding and an
  operational CR has no review, so an approving verdict, a refusal
  and silence are equally irrelevant — the record binds the commit
  the operator named, which is what ADR-0022 section 2 gives the
  fields.
- **Every refusal is decided before the write.** Flag combinations at
  the parser and in `_run_accept`, then task admission, the manifest
  and the commit resolution, then `create_acceptance_record` and
  `write_record` — `write_record`'s own validation is the last thing
  to run, so a refused run leaves the journal untouched.
- **The output is the findings form's.** The record's path, printed —
  nothing else; a resolved `<rev>` is visible in the record itself.

## Risks

- [A pause acceptance for an extension nobody declared] → the manifest
  check refuses naming the extension before the write; the record
  layer's name rule would refuse a name that is not one path
  component anyway, and the manifest reader runs that rule first.
- [A form flag silently widening the findings path] → the combos are
  refused naming the flags, and the findings form's tests stand
  untouched.
- [A symbolic `--commit` binding to something the operator did not
  mean] → `rev-parse --verify <rev>^{commit}` names the resolution
  failure, and the record carries the resolved full id a reader can
  check.
- [A refusal leaving a record behind] → every refusal precedes
  `write_record`; the tests snapshot the journal tree around refused
  runs.
