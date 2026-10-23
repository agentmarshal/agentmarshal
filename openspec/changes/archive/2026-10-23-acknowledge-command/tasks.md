## 1. The command

- [x] 1.1 `src/agentmarshal/acknowledge.py` defines `register` adding
  `acknowledge` with `--task`, `--base`, `--commit`, `--file`,
  `--reason` required and `--signature`/`--marker` a required
  mutually-exclusive pair, and `run` executing it — verify:
  `acknowledge --help` lists the arguments (pytest).
- [x] 1.2 `cli.py` imports the module, registers it beside `agree` and
  `record-check` and dispatches `args.command == "acknowledge"` to
  `acknowledge.run` — verify: the dispatch is one `if` per module, no
  other command touched (read, pytest).

## 2. The scan is `leak-scan`'s own

- [x] 2.1 The command resolves the merge base of `--base` and
  `--commit` in the scanned repository (`placement.host_root` — the
  host under a sidecar, resolved with `require_host=True`), reads the
  markers the way `_run_leak_scan` does (`markers_from_config` on the
  sidecar's configuration under a sidecar, `markers_from_tree` at the
  merge base otherwise), takes the diff through `leak_scan_diff` and
  the hits through `scan_diff_for_leaks` with the same `config_path` —
  verify: the tests whose docstrings name the signature, the marker and
  the marker-named-path scenarios (pytest).
- [x] 2.2 The record writes only when a hit's `path` equals `--file`
  and its `identification` equals `--signature` or `private-marker
  #<n>` — string equality, no other matching; a mismatch is refused
  naming the file and the identification given and how many hits the
  scan reported, never the matched text — verify: the tests whose
  docstrings name the printed-name, wrong-identification, other-commit
  and clean-scan scenarios (pytest).
- [x] 2.3 Files the scan could not decode are named on stderr through
  `render_undecodable_files`, no hit and no failure on their own —
  verify: the test whose docstring names the undecodable-file scenario
  (pytest).
- [x] 2.4 `leak-scan`'s behaviour, output and exit are untouched —
  verify: the test whose docstring names the unchanged-standalone
  scenario plus the existing `test_leak_scan.py` suite (pytest).

## 3. Writing the record

- [x] 3.1 `acknowledge` writes one `acknowledgement` record through
  `create_acknowledgement_record` with `--commit` resolved to its full
  40-hex id via `git rev-parse --verify <rev>^{commit>` in the scanned
  repository, and prints the record's path, the commit, the file, the
  identification and the recorder — verify: the tests whose docstrings
  name the write and the resolving scenarios (pytest).
- [x] 3.2 Lifecycle admission is `load_task_for_record(...,
  "acknowledgement")` — an unknown task is refused naming it, a
  completed or abandoned task is refused naming its state — verify:
  the tests whose docstrings name the unknown and the terminal
  scenarios (pytest).
- [x] 3.3 A commit that resolves to no commit is refused naming it; a
  base and a commit sharing no merge base are refused naming both —
  verify: the tests whose docstrings name the two scenarios (pytest).
- [x] 3.4 The record passes `validate_record_for_write` before the hit
  is matched, so a value the record rules refuse — the reason's
  1000-character bound, an empty field, an unknown signature, a marker
  below 1 — is refused on the rule, writing nothing — verify: the test
  whose docstring names the record-rules scenario (pytest).
- [x] 3.5 The recorder resolves through `resolve_recorded_by` before
  `write_record`: none resolved refuses writing nothing; a recorder
  who is not a declared actor is written with a note saying so;
  declared is tested on the id against the project file's `actors`;
  the recorder prints through `escape_for_display` — verify: the tests
  whose docstrings name the unresolved, undeclared, declared and
  escaping scenarios (pytest).
- [x] 3.6 Every refusal leaves the journal byte-identical and the
  journal still validates — verify: the snapshot assertions in the
  refusal tests, `main(["validate"])` after refusal (pytest).

## 4. Nothing that worked changed

- [x] 4.1 `status`, `validate` and the gate treat the command's records
  as they already treat `acknowledgement` records, and the gate's
  fixtures and pinned transcripts are unchanged — verify: the full
  suite, including `test_acknowledgement.py` and the transcript pins,
  stays green (pytest).
- [x] 4.2 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`, and the suite again
  under CI conditions — no actor override, no git identity — verify:
  run them.
