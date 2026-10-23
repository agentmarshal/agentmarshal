## 1. The read

- [x] 1.1 `cli.py`'s `leak-scan` parser gains an optional `--task <id>`
  — verify: `leak-scan --help` lists it (pytest).
- [x] 1.2 `_run_leak_scan` resolves the candidate with `git rev-parse
  --verify <commit>^{commit}` in `scan_root` and reads the journal's
  `acknowledgement` records for that commit — `load_task_status` for a
  `--task`, `list_task_statuses` over `placement.journal_root`
  otherwise — verify: the tests whose docstrings name the every-task,
  the `--task` and the closed-task scenarios (pytest).
- [x] 1.3 Any read failure — commit that cannot be resolved, unknown or
  unreadable `--task`, a record that fails validation, a journal that
  cannot be listed — prints `leak-scan: cannot read acknowledgements:
  <why>` on stderr, escaped, and acknowledges nothing; a repository
  with no project skips the read, a `--task` there is said instead —
  verify: the tests whose docstrings name the unreadable-task,
  unreadable-journal and no-journal scenarios (pytest).

## 2. The match

- [x] 2.1 A record acknowledges a hit when its `file` equals `hit.path`
  and its identification — `signature`, or `private-marker #<n>` for
  `marker` — equals `hit.identification`, the earliest matching record
  in journal order marking the hit; no other matching — verify: the
  tests whose docstrings name the bound-hit, marker-number,
  other-commit, differently-spelled-file, other-identification and
  earliest-record scenarios (pytest).

## 3. The print and the exit

- [x] 3.1 `render_leak_hits` gains an optional per-hit `marks`
  parameter appended to the hit's entry in parentheses; the gate's
  call is unchanged and renders byte for byte — verify: the pinned
  gate transcripts and the test whose docstring names the boundary
  scenario stay green (pytest).
- [x] 3.2 The command passes `acknowledged by <recorded_by>: <reason>`
  — each through `escape_for_display` — for the hits its records name,
  every hit still printed in today's order; exit 0 when all are
  acknowledged, 1 when any is not, today's behaviour on a clean scan —
  verify: the tests whose docstrings name the marked, ordered,
  escaped, never-printed, exits-0, exits-1, clean-scan and
  byte-for-byte scenarios (pytest).

## 4. Nothing that worked changed

- [x] 4.1 No other command changes; the gate's fixtures and pinned
  transcripts are unchanged; the existing `test_leak_scan.py` and
  `test_acknowledge.py` suites stay green — verify: the full suite,
  including in CI's conditions (`env -u AGENTMARSHAL_ACTOR
  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1`) (pytest).
- [x] 4.2 Full check sequence passes: `uv sync --locked`,
  `uv run agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy` — verify: run them.
- [x] 4.3 The change is archived with `openspec archive` — verify:
  `openspec/changes/archive/` holds it and `openspec/specs/leak-scan/`
  carries the new text.
