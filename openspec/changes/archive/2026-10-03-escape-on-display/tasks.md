## 1. The escape

- [x] 1.1 `agentmarshal.journal.display.escape_for_display` renders every
  character `forges_rendered_text` refuses as `\n`, `\r`, `\t` or
  `\uXXXX`/`\UXXXXXXXX` and leaves every other character — verify: a test
  derives its cases from the predicate itself.
- [x] 1.2 `status` escapes every string taken from a record or a contract,
  the task list and the per-task view — verify: a test gives the view
  in-memory records today's read rules would refuse on disk and shows each
  printed escaped on its one line.
- [x] 1.3 `report` escapes every such string — verify: the same kind of
  in-memory test over `format_report`.

## 2. Nothing that worked changed

- [x] 2.1 Records without refused characters print byte-identically: the
  existing status and report tests pass unchanged, and the full status pin
  test gains the `completed` line with a finding reference it lacked (a
  carried advisory) — verify: pytest.
- [x] 2.2 The full CI sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
