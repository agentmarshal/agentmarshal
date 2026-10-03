## 1. The writers pin the contract's hash

- [x] 1.1 `open_task` computes `contract_sha256` over the contract text it
  writes and passes it to `create_opened_record` — verify: the `opened`
  record carries the hash and stamps schema 7 (pytest).
- [x] 1.2 `amend` hashes the task's `contract.md` as it stands — the
  journal repository's copy in a sidecar — pins it, and refuses a
  contract that does not parse — verify: pytest, including the sidecar
  placement.
- [x] 1.3 `migrate` pins the hash of each contract it writes — verify:
  pytest.

## 2. `open` takes a contract already written

- [x] 2.1 `--contract-file` reads, validates (`parse_contract_text`) and
  retargets the header `id` to the assigned task id, writes the file as
  the task's contract and pins its hash; a different replaced value is
  named on stderr — verify: pytest.
- [x] 2.2 `--contract-file` refuses `--title`/`--scope` and a missing,
  unreadable or invalid file, writing nothing — verify: pytest.

## 3. `status` shows the drift

- [x] 3.1 `status <task>` prints one line — both short hashes and the
  `amend` reminder — when the contract differs from the latest
  `opened`/`amendment` pin, nothing when they match or no record carries
  a hash, and never fails because of the drift — verify: pytest.

## 4. Documentation and spec

- [x] 4.1 `docs/quickstart.md` opens the task from a contract written
  first and says what an edit after `open` does — verify:
  `test_quickstart.py` runs the blocks and the pinned transcript matches.
- [x] 4.2 The contract-governance delta states the writers', the
  `--contract-file` and the drift requirements and modifies the one the
  writers' obligation makes untrue as stated — verify: the change
  validates and archives.
- [x] 4.3 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
