## 1. The command

- [x] 1.1 `src/agentmarshal/agree.py` defines `register` adding `agree`
  with `--task` required and `--contract` optional, and `run` executing
  it — verify: `agree --help` lists both arguments (pytest).
- [x] 1.2 `cli.py` imports the module, registers it beside `steps` and
  dispatches `args.command == "agree"` to `agree.run` — verify: the
  dispatch is one `if` per module, no other command touched (read,
  pytest).

## 2. Writing the agreement

- [x] 2.1 `agree` writes one `agreement` record whose `contract` is
  `contract_sha256(contract.md read as bytes)` — in a sidecar the
  journal repository's copy — prints the record path, the hash and the
  recorder, and admits a second agreement on the same task — verify:
  the tests whose docstrings name the write and the repeat scenarios
  (pytest).
- [x] 2.2 `--contract` not exactly 64 lowercase hex is refused naming
  the field before the journal is touched; a well-formed value unequal
  to the current hash is refused naming both; an equal value writes at
  that hash — verify: the tests whose docstrings name the three
  scenarios (pytest).
- [x] 2.3 The current hash is compared against the latest
  hash-carrying `opened`/`amendment` record — restated locally from the
  task's records, the same scan `status_view` makes for its drift line;
  drift refuses naming both short hashes and `amend`, while no pin
  agrees at the current text — verify: the tests whose docstrings name
  the drift, the no-pin and the latest-pin scenarios (pytest).
- [x] 2.4 Lifecycle eligibility is `load_task_for_record(...,
  "agreement")` — an unknown task or a terminal projection refuses
  naming the reason, a check after completion reopens nothing — verify:
  the tests whose docstrings name the unknown, terminal and
  check-after-completion scenarios (pytest).
- [x] 2.5 The recorder resolves through `resolve_recorded_by` before
  `write_record`: none resolved refuses writing nothing; a recorder who
  is not a declared actor is written with a note saying so; declared is
  tested on the id against the project file's `actors`, so an override
  naming a declared actor prints no note — verify: the tests whose
  docstrings name the unresolved, undeclared and declared scenarios
  (pytest).
- [x] 2.6 The recorder prints through `escape_for_display` on stdout
  and in the stderr note; refusals print on stderr — verify: the test
  whose docstring names the escaping scenario (pytest).
- [x] 2.7 Every refusal leaves the journal byte-identical and the
  journal still validates — verify: the snapshot assertions in the
  refusal tests, `main(["validate"])` after refusal (pytest).

## 3. Nothing that worked changed

- [x] 3.1 `status`, `validate` and the gate treat the command's records
  as they already treat `agreement` records — verify: the full suite,
  including `test_agreement.py`'s admitted-after-terminal and
  status/validate scenarios, stays green (pytest).
- [x] 3.2 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`, and the suite again under
  CI conditions — no actor override, no git identity — verify: run
  them.
