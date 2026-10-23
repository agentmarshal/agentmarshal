## Context

ADR-0021 decision 2 recorded what an acknowledgement binds: the
candidate's commit, the file, and the hit's identification exactly as
the scan prints it — a signature id or a private marker's number, never
the matched text — plus a reason, and the recorder as every record's
attribution. ADR-0022 section 3 gave the record its schema-7 shape and
its rules: `signature` xor `marker`, `reason` to 1000 characters,
`recorded_by`/`recorded_by_source` required, not admitted after a
terminal record. CR-170 landed all of it; nothing writes the record.

The pieces this command composes all exist:
`create_acknowledgement_record` builds the record;
`load_task_for_record` answers lifecycle admission; the scan
`leak-scan` runs is `markers_from_tree`/`markers_from_config` for the
configured markers, `leak_scan_diff` for the per-file-decoded
`merge-base..commit` diff and `scan_diff_for_leaks` for the hits, and
`LeakHit` already carries the file and the identification exactly as
the command prints them — `path` masked through `safe_path`,
`identification` a signature id or `private-marker #N`.

An acknowledgement binds a hit only on the same commit, file and
identification (ADR-0021 decision 2), so a record naming a hit the scan
never reported would match nothing and say something false. That is why
the command checks the hit against the scan before writing rather than
trusting the flags.

## Goals

- `agentmarshal acknowledge --task <id> --base <ref> --commit <rev>
  --file <path> (--signature <id> | --marker <n>) --reason <text>`
  writes one `acknowledgement` record: the commit resolved to its full
  40-hex id, and the record lands only when the scan reports a hit with
  exactly that file and that identification.
- The scan is `leak-scan`'s own — the same helper functions over the
  same inputs — so the hit being checked is the hit the standalone
  command reports, under either placement.
- Every refusal writes nothing and names its reason; a recorder that is
  not a declared actor is accepted and named as such.

## Non-Goals

- `leak-scan`, the gate and `status` honouring and marking acknowledged
  hits — later tasks. This change writes records; no reader's output
  changes.
- Acknowledging the artefact-capture refusal — it names categories and
  no file, so there is nothing to bind (ADR-0021 decision 2).
- Roles, or any rule about who may acknowledge (ADR-0021 decision 4);
  self-acknowledgement is permitted and its mark is derived on display,
  not stored.
- Protection beyond the published threat model — including against a
  process of the same OS user.

## Decisions

- **One module, `acknowledge.register` + `acknowledge.run`.** The
  command lives in `src/agentmarshal/acknowledge.py` and registers into
  `cli.py`'s subparsers the way `steps`, `agree` and `record-check` do
  — one dispatch `if` per module. `--signature`/`--marker` is an
  argparse mutually-exclusive group marked required: both or neither
  exits before the command runs, writing nothing.
- **The scan is the standalone command's, restated call for call.**
  The merge base of `--base` and `--commit` is resolved in the scanned
  repository — `placement.host_root`, the host under a sidecar, where
  the candidate's commits live — the markers come from the trusted
  side exactly as `_run_leak_scan` reads them (`markers_from_config` on
  the sidecar's own configuration under a sidecar, `markers_from_tree`
  at the merge base otherwise), the diff is `leak_scan_diff`'s, and the
  hits are `scan_diff_for_leaks`' with the same `config_path` the
  command passes. No second scanner exists for the two to drift apart.
- **The commit is resolved in the scanned repository.** `git rev-parse
  --verify <rev>^{commit}` under `host_root`: the record's `commit` is
  the candidate's full id, which a sidecar's own repository does not
  hold — resolving it in the journal's repository the way
  `record-check` does would refuse exactly the commits an
  acknowledgement exists for. A `--base` or `--commit` that resolves to
  no commit, or shares no merge base, is refused naming the
  reference(s).
- **The match is the hit exactly as the scan prints it.** A hit equals
  what was given when `hit.path == --file` and `hit.identification`
  equals `--signature`, or `private-marker #<n>` for `--marker <n>` —
  string equality on the already-masked path, no normalisation, no
  globbing, no case folding: a file that carries a marker is
  acknowledged under its printed masked name, and a spelling the scan
  never printed matches nothing. A mismatch is refused naming the file
  and the identification given and how many hits the scan reported —
  the count, never the hit list, and never the matched text.
- **Refusal order: task, commit and merge base, record, the hit.**
  `load_task_for_record(..., "acknowledgement")` answers lifecycle
  admission — an unknown task is refused naming it and a completed or
  abandoned task is refused naming its state, the record type being
  admitted after no terminal record. The recorder resolves and the
  record passes `validate_record_for_write` — shape, the signature
  vocabulary, `marker` at least 1, the reason's bound, the
  forgeable-text rule, a resolvable recorder — before the hit is
  matched, so a value the record rules refuse is refused on the rule
  rather than reported as a missing hit. The reason lands in the
  record, so it passes `scan_for_leaks` with the project's markers the
  same way: a hit is refused naming the categories — never the text —
  and the operator re-words the reason. The hit match is last: only a
  writable record naming a reported hit reaches `write_record`, and
  every refusal leaves the journal byte-identical.
- **A file the scan could not decode is named, not counted.** The
  `leak_scan_diff` caller's second return is reported on stderr as the
  standalone command reports it — masked through
  `render_undecodable_files` — since a partial read is exactly why a
  hit an operator expected can be absent; it is a caveat about the
  scan, never a hit, and it fails nothing on its own.
- **Output names what it must and escapes what it must.** The record
  path, the resolved commit, the file, the identification and the
  recorder print on stdout; refusals, the undecodable-file caveat and
  the undeclared-actor note print on stderr. The recorder and git's own
  error text pass through `escape_for_display`; the other printed
  values already passed the record's own forgeable-text refusal, and a
  signature id is the scan's vocabulary by construction.

## Risks

- [A second scanner drifting from `leak-scan`'s] → there is none: the
  command calls `leak_scan_diff` and `scan_diff_for_leaks` with the
  same arguments `_run_leak_scan` computes, so the check cannot read a
  different diff or different markers than the command reports.
- [An acknowledgement recorded against a hit the scan never reported]
  → the record lands only through the match on the scan's own output —
  commit, file and identification all three — so a mistyped file or a
  renumbered marker list is a visible refusal, never a silently false
  record.
- [`--file` or git's stderr forging a transcript line] → file values
  that could forge a line die at the record's forgeable-text refusal
  before the match message can print them, and every other
  untrusted value is escaped where it prints.
- [The standalone command's output or exit drifting] → `leak-scan` is
  not touched: the change adds a caller of the scan's helpers beside
  it, and the existing tests pinning the gate transcript and the
  standalone output stay green.
