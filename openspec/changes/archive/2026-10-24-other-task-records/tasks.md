## 1. The gate warning

- [x] 1.1 `run_gate` gathers the candidate-added `opened` and
  `amendment` record paths whose task directory names a task other than
  the one judged, groups them by task and kind, and prints one WARN
  line naming each task and its kinds — verify: the tests whose
  docstrings name each scenario (pytest).
- [x] 1.2 The warning counts nothing against the candidate: no
  violation, no refusal, and a candidate adding no such record prints
  today's transcript byte for byte — verify: the scenario tests and the
  pinned fixtures (pytest).

## 2. The `status --base` listing

- [x] 2.1 `records_absent_from_ref` resolves `<ref>` to a commit in the
  journal's own repository — the project repository embedded, the
  sidecar repository under a sidecar placement — and lists the task's
  stored record paths that ref's tree does not hold, reading the tree
  with NUL-separated `ls-tree` under a literal pathspec — verify: the
  scenario tests, including the sidecar one (pytest).
- [x] 2.2 `status <task> --base <ref>` prints the detail view it prints
  today followed by the listing — a header naming the ref, one `- <id>
  <type>` line per absent record, or one line saying there are none —
  every printed value escaped; `--base` without a named task refuses,
  and an unresolvable ref refuses naming it before any view output —
  verify: the scenario tests (pytest).
- [x] 2.3 Without `--base` the command prints exactly what it prints
  today — verify: the byte-for-byte pin (pytest).

## 3. The change itself

- [x] 3.1 proposal.md, design.md, tasks.md and the gate-lanes and
  record-lifecycle delta specs are written — verify: openspec validate.
- [x] 3.2 Every scenario in the delta specs is demonstrated by a test
  whose docstring names it — verify: grep the test docstrings against
  the specs' scenario headings.
- [x] 3.3 Full check sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`, `uv run
  ruff format --check`, `uv run mypy` — and the CI-conditions run
  `env -u AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null
  GIT_CONFIG_NOSYSTEM=1 uv run pytest -q`.
- [x] 3.4 The change is archived with the archive command — verify:
  `openspec/specs/gate-lanes/spec.md` and
  `openspec/specs/record-lifecycle/spec.md` gain each new requirement
  once and the change lives under `openspec/changes/archive/`.
