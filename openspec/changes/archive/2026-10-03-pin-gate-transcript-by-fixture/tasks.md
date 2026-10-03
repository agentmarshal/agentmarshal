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
  run through `test_regenerate_the_committed_fixtures`, which skips
  without the flag; unset, nothing writes — verify: a test named for the
  scenario.
- [x] 1.5 Outside the update path all three fixture files of a case must
  exist — a missing fixture fails the test naming it, never compares as
  an empty stream — verify: the fixture-lifecycle test asserts the
  failure names the absent files.
- [x] 1.6 The full commit sha and its twelve-character abbreviation map to
  different placeholders (`<head-sha>`/`<head-sha-12>`, likewise for
  base); the pinning test removes `AGENTMARSHAL_UPDATE_GATE_FIXTURES`
  from its own environment — verify: read; the regenerated fixtures
  differ from the previous ones only in the placeholder names.

## 2. What the pin replaces

- [x] 2.1 The two byte-for-byte comparisons against the released 0.3.0
  binary are removed; `released_030`/`SKIP_030` stay for the schema tests
  in `test_findings.py`/`test_journal.py` — verify: grep finds no
  transcript comparison left, `uv run pytest -q` passes.
- [x] 2.2 The scenario-naming delegates (the default-run test, the
  without-renames test and the old-journal test) point at the fixture
  test, docstrings updated — verify: read.
- [x] 2.3 No other gate test changes — verify: `git diff tests/` touches
  only what this change names.

## 3. The other scenarios that promised a 0.3.0 transcript

- [x] 3.1 A MODIFIED delta restates scope-enforcement's "a candidate
  without renames prints the transcript it printed before" against the
  committed fixtures, keeping every requirement and scenario header —
  verify: `test_a_candidate_without_renames_prints_the_transcript_it_printed_before`
  names the scenario and delegates to the fixture pin.
- [x] 3.2 A MODIFIED delta restates review-evidence's "an old journal
  reads as before" against the committed fixtures — verify:
  `test_old_journal_reads_as_before` holds the gate transcript of a
  candidate whose review record carries no `artifacts` to the committed
  fixture.
