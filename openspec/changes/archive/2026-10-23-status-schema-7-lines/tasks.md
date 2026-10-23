## 1. The renderers

- [x] 1.1 `RecordRenderer` gains the journal root and the dispatch passes
  it; the four renderers — `_render_check_line`,
  `_render_agreement_line`, `_render_acknowledgement_line`,
  `_render_ext_line` — register under their record types — verify: the
  tests whose docstrings name each record line's scenario (pytest).
- [x] 1.2 `_recorder_clause` names the recorder and marks a recorder
  that is not a declared actor, testing `recorded_by` against the
  `actors` keys of the project file the journal belongs to — verify:
  the declared/undeclared recorder tests (pytest).
- [x] 1.3 `_is_self_acknowledged` derives the mark through the same
  commit-writers query as `_is_self_accepted`, returning `None` where
  git cannot answer and rendering "the mark was not checked" — verify:
  the self-acknowledged, other-actor and unreadable-commit tests
  (pytest).

## 2. The agreement line

- [x] 2.1 `_agreement_line` prints after the records: "no agreement is
  recorded" when the task carries none, the earlier-text line naming
  both short hashes when the latest agreement's hash differs from the
  contract's current hash, nothing otherwise — verify: the tests whose
  docstrings name the three scenarios (pytest).
- [x] 2.2 The comparison is against the contract's current hash, not
  the pin — verify: the drifted-contract test whose agreed hash still
  equals the pin prints the earlier-text line (pytest).

## 3. Everything else is unchanged

- [x] 3.1 Every value the four lines take from a record prints escaped;
  output of every other record type, the header, the drift line, the
  overdue-step and path output is unchanged — verify: the byte-exact
  escaping pin in `test_status_schema_7_lines.py`, the existing pins in
  `test_status_view.py`, `test_display.py` and `test_status_steps.py`
  extended by the agreement line only (pytest).
- [x] 3.2 `docs/sidecar.md`'s `status` example gains the agreement
  line — verify: read the example.
- [x] 3.3 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
