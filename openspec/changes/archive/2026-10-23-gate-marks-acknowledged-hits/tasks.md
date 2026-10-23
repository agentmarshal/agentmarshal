## 1. The shared mark

- [x] 1.1 `_acknowledgement_identification` and `_acknowledgement_mark`
  move verbatim from `cli.py` into `capture.py` beside
  `render_leak_hits`, `escape_for_display` imported where it runs —
  display.py stands on capture.py through records.py, so a top-level
  import back would cycle. `cli.py` stays outside this task's scope,
  so its private copies remain for the one-line switch a later task
  lands — verify: `leak-scan`'s acknowledgement suite and the pinned
  transcripts stay green (pytest).

## 2. The gate's line

- [x] 2.1 In the advisory block, `task.records` is filtered to
  `acknowledgement` records whose `commit` equals `resolved_commit`;
  `_acknowledgement_mark` builds one mark per hit over the same
  markers the scan used, and `render_leak_hits` gets the `marks`
  beside the unchanged `limit=_LEAK_HIT_RENDER_LIMIT` — verify: the
  tests whose docstrings name the marked, same-mark, masked, escaped,
  earliest-record, other-commit, other-task, other-file and
  other-identification scenarios (pytest).
- [x] 2.2 The bound is the line's own: at most twenty shown, then
  "and N more not shown" — a hit past the bound takes no mark; an
  acknowledgement removes no hit and changes no order; a marked hit
  adds no violation; no acknowledgement renders the line byte for
  byte — verify: the tests whose docstrings name the bound, order,
  no-violation and byte-for-byte scenarios plus the pinned gate
  transcripts (pytest).

## 3. Nothing that worked changed

- [x] 3.1 No other gate check changes; no command changes; the gate
  fixtures under `tests/fixtures/` are untouched and the interim
  "carries no mark yet" scenario test is updated to the revised
  scenario — verify: the full suite, including in CI's conditions
  (`env -u AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null
  GIT_CONFIG_NOSYSTEM=1`) (pytest).
- [x] 3.2 Full check sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
- [x] 3.3 The change is archived with `openspec archive` — verify:
  `openspec/changes/archive/` holds it and
  `openspec/specs/leak-scan/` carries the new text.
