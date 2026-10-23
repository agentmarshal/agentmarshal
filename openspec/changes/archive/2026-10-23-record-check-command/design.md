## Context

ADR-0017 decision 1 made a pipeline's verdict evidence: a `check`
record carries the commit, the check's name, its result
(`passed` | `failed` | `error` | `skipped`), the step that failed, a
bounded excerpt through the leak scan, and a run link — a measurement
admitted after any terminal record (ADR-0022 section 3). CR-167
registered the record type and `create_check_record`; the
`check-output` process-log event (ADR-0022 section 7) holds the full
output, which the journal never keeps. The primitives this command
composes all exist: `write_payload`/`write_event` on the journal
repository's local state — the mechanism the review launcher keeps
`review-prose` with — `load_task_for_record` for lifecycle
admission, `resolve_recorded_by` for the required recorder, and the
leak scan's signature table and the project's `private_markers` in
`capture.py`.

## Goals

- `agentmarshal record-check --task <id> --commit <rev> --name <check>
  --result <result>` writes one `check` record: the commit resolved to
  its full 40-hex id in the journal's repository, plus optional
  `--failed-step` and `--run-url`.
- `--output-file` keeps the whole output in the clone's local state —
  never versioned — and announces it with a `check-output` event
  carrying the task, the name, the commit, the kept path and its
  sha256; the record's `excerpt` is the content's tail bounded at
  4 KiB *after* masking.
- A leak-scan hit in the excerpt masks the matched span to
  `[masked: <category>]`; the record is still written — refusing it
  would lose the fact the record exists to keep — and the command
  names the categories, never the matched text.
- Every refusal writes nothing: no record, no event, no kept file.

## Non-Goals

- `brief` naming the last failed check and `report` counting refusals
  — later tasks.
- A CI integration that calls the command; provider templates.
- Masking or scanning the full output kept in local state (ADR-0017:
  the unmasked output stays on the machine that ran the check).
- Protection beyond the published threat model — the local state
  resists nothing from a process of the same OS user.

## Decisions

- **One module, `record_check.register` + `record_check.run`.** The
  command lives in `src/agentmarshal/record_check.py` and registers
  into `cli.py`'s subparsers the way `steps` and `agree` do — one
  dispatch `if` per module.
- **The commit resolves in the journal's repository, before anything
  else that can fail.** `git rev-parse --verify <rev>^{commit}` run in
  `placement.project_root` — the repository that holds the journal in
  either placement, so a sidecar records against the commits its own
  repository carries, never the host's. What resolves is the full id
  the record's 40-hex rule already requires; what does not is refused
  naming the reference, and git's own error text is escaped before it
  is printed.
- **Refusal order: argument shape, task, commit, output file, record
  preflight, recorder.** `--result` outside the vocabulary and a
  malformed task id fail before the journal is read;
  `load_task_for_record(..., "check")` answers lifecycle admission —
  an unknown task is refused naming it, a completed or abandoned task
  admits the measurement, and no second admission list appears. An
  unreadable `--output-file` is refused before anything is written.
  `validate_record_for_write` then applies every record refusal
  knowable before an exclusive write — an empty `--name`, a forgeable
  `--run-url`, a missing recorder — so the payload, the event and the
  record itself are the only writes left, and every refusal leaves the
  journal, the log and `files/` untouched.
- **The recorder resolves before the payload is written.** The record
  requires `recorded_by`/`recorded_by_source`; resolution is decided
  ahead of `write_payload` rather than left to `write_record`, so a
  missing identity costs no kept file. A recorder who is not a
  declared actor is accepted with a stderr note saying so — the same
  wording `agree` gives, through the same `_declared_actor` test.
- **The excerpt is the tail, masked, escaped, and bounded on
  characters.** The output decodes whole with `errors="replace"` —
  every undecodable byte lands as the replacement character under
  Python's own decoder, so no hand-rolled byte logic ever halves a
  character or misreads an invalid sequence — and the failing end of a
  log is the part worth keeping. The text then passes through
  `mask_leaks`, then `escape_for_display` — the record's
  forgeable-text rule refuses newlines outright, and a check output's
  tail is exactly the lines that failed — and is kept to the longest
  suffix of whole characters encoding to at most 4 KiB of UTF-8: a
  `[masked: …]` token or an escape can be longer than the span it
  replaces, so the bound is measured after the masking, the excess
  dropping from the front. An excerpt that comes out empty or all
  whitespace is omitted — the record admits `excerpt` only non-empty.
- **An excerpt masking cannot make clean is withheld.** A marker that
  occurs in the mask label itself still trips the scan after masking;
  the record then carries no `excerpt` — never the marker's value —
  the command says the excerpt was withheld, and stderr still names
  the categories found.
- **Mask first, escape second, both after the decode.** Masking sees
  the text in its true form — a private marker that itself carries a
  newline still matches — and the escapes produced afterwards are
  plain ASCII that no signature or marker can recompose into. The full
  output kept in local state is never masked: it is the same
  machine's private file, and masking it would falsify the very thing
  the excerpt cites.
- **`mask_leaks` lives beside `scan_for_leaks` and shares its
  vocabulary.** One table of signatures drives both; a private marker
  is masked before the signatures run — the marker is the sensitive
  string and masking it whole can never leave a signature-shaped
  fragment of itself behind — and the replacement token is
  `[masked: <category>]` with `private-marker` as a marker's category,
  the same name `scan_for_leaks` reports. The function returns the
  masked text and the sorted categories; the command prints the
  categories on stderr and the matched text nowhere.
- **The payload and the event mirror `_local_state_output`'s
  mechanism, with the check's own fields.** `local_state(
  resolve_placement(...))` resolves the journal repository's local
  state — a sidecar's own, the host never entering — `write_payload`
  keeps the bytes under `log/files/` with a
  `agentmarshal-check-output-` prefix, and `write_event` appends
  `check-output` carrying `task`, `name`, `commit`, `path` and
  `sha256`. The record's own fields cannot ride the event: the check
  name and the resolved commit are what a reader of the log needs to
  place the file.
- **Local-state failure degrades like review prose, not to a
  refusal.** When the local state cannot be used — git cannot name
  the common directory, a directory cannot be created — the output is
  kept in a local temporary file and stderr names the path and the
  reason, exactly as the review launcher reports it; the check's
  result is the fact being recorded and is never discarded because
  preservation failed. The event is written only where the log could
  hold it.
- **The record writes last, and a failure names what it left.** With
  the payload and event already down, a record write that fails — a
  filesystem error, an id collision — reports the failure and names
  the kept file, the way `submit_review` names a left artifact: an
  orphan the operator can find is a named limit, not a hidden one.
- **Output names what it must and escapes what it must.** The record
  path, the resolved commit, the check's name and its result print on
  stdout; the kept-file note, the masking categories, the
  undeclared-actor note and every refusal print on stderr. The
  recorder passes through `escape_for_display`; the check's fields
  already passed the record's own forgeable-text refusal, and git's
  error text is escaped where it is shown.

## Risks

- [A mask token longer than its span pushes the excerpt past 4 KiB] →
  the excerpt is bounded after masking to the longest character suffix
  within 4 KiB, so the record's byte rule always holds and the failing
  end survives.
- [A multi-byte character straddling the tail cut decodes as a false
  replacement char] → the whole output decodes through Python's own
  `errors="replace"` and the suffix counts whole characters, so a
  character is either whole or absent.
- [A private marker containing a refused character would never match
  post-escape text] → masking runs on the decoded text before
  escaping, so the marker's literal form is what is matched.
- [A local-state failure after the payload lands could orphan a kept
  file] → the event follows the payload in one block, and a record
  failure afterwards names the kept file; the payload itself is
  append-only local state, never evidence.
- [The gate transcript or `leak-scan` output drifting] → neither is
  touched: the masking is a new function beside the scan, and the
  existing tests pinning both surfaces stay green.
