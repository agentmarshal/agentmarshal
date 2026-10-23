## 1. The command

- [x] 1.1 `src/agentmarshal/record_check.py` defines `register` adding
  `record-check` with `--task`, `--commit`, `--name`, `--result`
  required and `--failed-step`, `--run-url`, `--output-file` optional,
  and `run` executing it — verify: `record-check --help` lists the
  arguments (pytest).
- [x] 1.2 `cli.py` imports the module, registers it beside `steps` and
  `agree`, and dispatches `args.command == "record-check"` to
  `record_check.run` — verify: one `if` per module, no other command
  touched (read, pytest).

## 2. Writing the record

- [x] 2.1 `record-check` resolves `--commit` through `git rev-parse
  --verify <rev>^{commit}` in the journal's repository and writes one
  `check` record through `create_check_record` at the resolved id,
  printing the record path, the commit, the name, the result and the
  recorder — a short or symbolic reference lands as its full 40-hex id
  — verify: the tests whose docstrings name the write and the
  resolution scenarios (pytest).
- [x] 2.2 `--result` outside `passed|failed|error|skipped` is refused
  before the command runs, writing nothing — verify: the test whose
  docstring names the vocabulary scenario (pytest).
- [x] 2.3 `--failed-step` and `--run-url` land as the record's
  `failed_step` and `run_url`; absent, the fields are absent —
  verify: the test whose docstring names the optional-fields scenario
  (pytest).
- [x] 2.4 Lifecycle admission is `load_task_for_record(..., "check")` —
  an unknown task is refused naming it; a completed or an abandoned
  task accepts the record — verify: the tests whose docstrings name
  the unknown-task and post-terminal scenarios (pytest).
- [x] 2.5 The recorder resolves through `resolve_recorded_by` before
  the payload is written: none resolved refuses writing nothing; a
  recorder who is not a declared actor is written with a note saying
  so; a declared actor prints no note — verify: the tests whose
  docstrings name the three scenarios (pytest).
- [x] 2.6 `validate_record_for_write` runs before any payload, event
  or record write — a value the record rules refuse leaves nothing —
  verify: the refusal tests' snapshot and log assertions (pytest).

## 3. The kept output and the excerpt

- [x] 3.1 `mask_leaks` joins `capture.py` beside `scan_for_leaks`:
  each configured marker replaced by `[masked: private-marker]`
  before the signatures run, each signature span by
  `[masked: <category>]` — the categories `scan_for_leaks` reports —
  returning the masked text and the sorted categories — verify: the
  unit tests on the function and the masking scenarios (pytest).
- [x] 3.2 `--output-file` keeps the file's full bytes through
  `write_payload` under the journal repository's `log/files/` and
  appends one `check-output` event carrying the task, the name, the
  resolved commit, the kept path and its sha256 — unmasked — verify:
  the tests whose docstrings name the payload and event scenarios
  (pytest).
- [x] 3.3 The excerpt is the content's last 4 KiB at most, cut on a
  character boundary with undecodable bytes replaced, masked, escaped
  and bounded to 4 KiB of UTF-8 again after masking — the failing end
  survives; an empty result omits `excerpt` — verify: the tests whose
  docstrings name the tail, the boundary, the undecodable-bytes and
  the bound-after-masking scenarios (pytest).
- [x] 3.4 Without `--output-file` the record carries no `excerpt` and
  no event lands — verify: the test whose docstring names that
  scenario (pytest).
- [x] 3.5 Local state that cannot be used keeps the output in a local
  temporary file, stderr saying why, and the record is still written —
  verify: the test whose docstring names the fallback scenario
  (pytest).
- [x] 3.6 An unreadable output file, an unknown task, an unresolvable
  commit, a result outside the vocabulary and a value the record rules
  refuse each write no record, no event and no kept file — verify:
  the tests whose docstrings name the refusal scenarios (pytest).

## 4. Nothing that worked changed

- [x] 4.1 `agentmarshal leak-scan`'s behaviour and output are
  unchanged and the gate's fixtures and pinned transcripts are
  untouched — verify: `test_leak_scan.py` and the fixture-pinning
  tests stay green, `tests/fixtures/` untouched (pytest).
- [x] 4.2 Full check sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`, `uv
  run ruff format --check`, `uv run mypy`, and the suite again under
  CI conditions — no actor override, no git identity — verify: run
  them.
