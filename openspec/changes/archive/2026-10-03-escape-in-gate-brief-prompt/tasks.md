## 1. The gate's transcript

- [x] 1.1 `run_findings_gate` and `run_gate` route every transcript line
  through `escape_for_display` — verify: a test gives the gate a candidate
  whose records carry a newline and a right-to-left override in their
  fields — built in memory, as a writer around the tool could — and shows
  each printed escaped on its own line.

## 2. The brief and the reviewer prompt

- [x] 2.1 `agentmarshal brief` escapes every value taken from a record or a
  contract — scope and acceptance entries, the task id, named decision,
  document and extension material, and the amendment history — verify: a
  test renders a brief over such values and shows each escaped.
- [x] 2.2 The reviewer prompt escapes every such value — the named contract
  material, the finding id, summary and artifact references, the
  undecodable-file names and the amendment history it carries — verify: the
  same kind of test over `_review_prompt` and `_finding_review_prompt`.
- [x] 2.3 Refusal and warning lines that quote a record or contract value
  print it escaped — verify: covered by the same tests' transcripts and
  prompts.

## 3. Nothing that worked changed

- [x] 3.1 Records and contracts without refused characters render
  byte-identically: the pinned gate fixtures, the pinned prompt tests and
  the contract-history "a task with no amendments is unchanged" scenario
  pass unchanged — verify: pytest.
- [x] 3.2 The full CI sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
