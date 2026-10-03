## 1. Errors and refusals escape what they carry

- [x] 1.1 `GateError` escapes its message at construction through
  `escape_for_display`, so every value carried into an error or refusal —
  a ref echoed in a failed git command, an exception's text, git's own
  error output — prints escaped, including messages raised by the gate
  context and ones a lifecycle or review wrapper re-quotes — verify: a
  run whose `--commit` carries a newline prints the ref escaped on
  stderr and raises the escaped message.

## 2. Candidate paths are named in escaped form

- [x] 2.1 A test commits a file whose name carries a newline and shows
  the scope line naming it escaped, with `gate: passed` printed nowhere
  it was not — verify: `test_a_candidate_path_that_would_forge_a_line_is_named_in_escaped_form`.
- [x] 2.2 A test commits a file whose name carries a right-to-left
  override and shows it named escaped — verify:
  `test_a_path_carrying_a_refused_character_is_named_in_escaped_form`.
- [x] 2.3 A test renames a newline-named file into scope and shows the
  scope line naming the source escaped — verify:
  `test_a_rename_source_carrying_a_refused_character_is_named_in_escaped_form`.
- [x] 2.4 Each test skips with a reason where the filesystem refuses
  such names — verify: read `_write_or_skip`.

## 3. Specs

- [x] 3.1 An ADDED delta gives record-text-safety the requirement that
  the gate escapes every value it did not write itself, each scenario
  demonstrated by a test whose docstring names it — verify: `openspec
  validate escape-gate-paths-and-errors --strict`.
- [x] 3.2 A MODIFIED delta restates scope-enforcement's "A candidate's
  change set names every path it touches" with paths named in escaped
  form, keeping every existing scenario — verify: the same.

## 4. Nothing that worked changed

- [x] 4.1 A candidate whose values carry no refused character renders
  byte-identically: the pinned gate fixtures and every existing gate
  test pass unchanged — verify: `uv run pytest -q` and the
  byte-identical delegate test.
- [x] 4.2 The full CI sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`, `uv run
  ruff format --check`, `uv run mypy` — verify: run them.
