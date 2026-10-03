## 1. The pin is a fixture

- [x] 1.1 Four fixture triples under `tests/fixtures/gate/` hold a default
  run's stdout, stderr and exit status: the implementation lane and the
  journal-only lane, each in the embedded and the sidecar placement —
  verify: the files exist and are plain text.
- [x] 1.2 One parametrized test builds each repository the way the existing
  gate tests build theirs (`_gate_repo`/`_implement`/`_approve`,
  `test_placement.py`'s `_commit`/`_host_and_sidecar`), runs
  `main(["gate", ...])` without the mode, and compares against the
  committed fixture — verify: pytest, with no `released_030` lookup.
- [x] 1.3 `_normalize_transcript` replaces run-dependent values with named
  placeholders — concrete values longest-first, record ids and times by
  pattern — and a mismatch reports a labelled unified diff — verify: the
  test names its scenario and a doctored transcript fails showing the
  differing line.
- [x] 1.4 `AGENTMARSHAL_UPDATE_GATE_FIXTURES` rewrites the fixtures from a
  run; unset, the test writes nothing — verify: a test named for the
  scenario.

## 2. What the pin replaces

- [x] 2.1 The two byte-for-byte comparisons against the released 0.3.0
  binary are removed; `released_030`/`SKIP_030` stay for the schema tests
  in `test_findings.py`/`test_journal.py` — verify: grep finds no
  transcript comparison left, `uv run pytest -q` passes.
- [x] 2.2 The scenario-naming delegates (the default-run test and the
  without-renames test) point at the fixture test, docstrings updated —
  verify: read.
- [x] 2.3 No other gate test changes — verify: `git diff tests/` touches
  only what this change names.
