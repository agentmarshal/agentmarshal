## Context

The pinned-transcript test in `tests/test_gate.py` builds a repository,
runs `main(["gate", ...])`, then runs a released 0.3.0 binary on the same
repository and compares stdout, stderr and exit status byte for byte.
`released_030()` finds the binary via
`AGENTMARSHAL_RELEASED_030`, `PATH`, or the default user-tool location; the
test skips when none reports 0.3.0. This repository's own governance
workflow installs only the locked uv environment, so the pin runs nowhere
in CI — and ADR-0022 lands a record schema the released binary cannot read,
which ends the comparison for good.

The transcript is nearly deterministic already: every line the gate prints
is a fixed string except the resolved commit's twelve-character
abbreviation, and nothing in it carries a record id, a timestamp or a path.
What varies is what the *test harness* varies — commit SHAs, the temporary
repository roots, and anything the setup prints that a future line might
quote.

## Goals

- The pin runs in every environment, with no external binary.
- The comparison is exact: everything but the enumerated run-dependent
  values must match, and a mismatch shows where.
- A task that changes the output on purpose regenerates the fixture, and
  the fixture's diff is part of that task's reviewed change — the output
  change gets a name.
- Repositories are built the way the existing gate tests build them.

## Non-Goals

- Any change to the gate's output or behaviour.
- Fixtures for lanes or modes other than the implementation lane and the
  journal-only lane (the findings lane and `--without-review` are not
  pinned).
- Fixtures for refused candidates other than the one the sidecar case
  produces — the refused empty-scope candidate keeps its existing
  behavioural test, not a fixture.

## Decisions

- **Four fixture triples, named by placement and lane.** Under
  `tests/fixtures/gate/`, each case is three plain text files:
  `<placement>-<lane>.stdout`, `<placement>-<lane>.stderr` and
  `<placement>-<lane>.exit`. Separate files keep each stream a plain text
  fixture and give a review diff that lands on the stream that changed.
  The cases:

  - `embedded-implementation` — `_gate_repo` + `_implement` + `_approve`,
    the passing diff-lane transcript.
  - `embedded-journal-only` — `_gate_repo` plus a committed journal-only
    change, the deterministic-lane transcript.
  - `sidecar-implementation` — a host and sidecar built with
    `test_placement.py`'s `_commit`/`_host_and_sidecar` helpers, an
    approved host change, the advisory diff-lane transcript.
  - `sidecar-journal-only` — a host candidate whose diff touches only
    `.agentmarshal/journal/` paths, built the way
    `test_sidecar_gate_gives_no_deterministic_lane_to_a_host_journal`
    builds it. The deterministic lane does not exist in a sidecar
    (`run_gate` forces `journal_only` off there — ADR-0008 Decision 2), so
    the fixture pins the transcript of the candidate that would take the
    lane in an embedded journal: the refusal that says it did not.

- **One substitution, applied to the actual output before comparison.**
  `_normalize_transcript` maps each run-dependent value to a named
  placeholder. Concrete values — the candidate and base commits in full
  and abbreviated form, the temporary repository roots — are replaced
  longest-first so an abbreviation is never claimed inside a longer value;
  record ids (26-character ULIDs) and ISO-8601 times are replaced by
  pattern, because a transcript line that ever prints one prints a fresh
  value each run. Everything else compares byte for byte: a changed word,
  a moved line, a new warning is a failed pin, not a substituted one.

- **A mismatch prints a unified diff.** The fixture text and the
  normalized run text are diffed per stream with labelled headers
  (`fixture` vs `actual`), so a failed pin names the lines that moved —
  the review of a deliberate change and the debugging of an accidental
  one read the same output.

- **Regeneration is an explicit environment flag.**
  `AGENTMARSHAL_UPDATE_GATE_FIXTURES`, set to a non-empty value other than
  `0`, makes the pinned test write the normalized transcript to the
  fixture files instead of only comparing. A task that changes the gate's
  output on purpose runs the test once with the flag set and commits the
  fixture diff with its change — that diff, in review, is the naming the
  requirement asks for. Without the flag the test never writes, so a
  fixture cannot drift in silence. The flag is honoured only in the
  pinned-transcript test; no other test can rewrite a fixture by accident.

- **The 0.3.0 transcript comparisons are removed, not kept.** Criterion 4
  permits keeping the released-binary comparison as an optional
  cross-check, but a cross-check that must equal today's output would
  fail precisely in the case this change exists for — a deliberate output
  change, where the released binary still prints the old transcript. Both
  comparisons are removed: the embedded diff-lane one and the empty-scope
  candidate's. `released_030` and `SKIP_030` stay: `test_findings.py` and
  `test_journal.py` use them for released-version *schema* behaviour,
  which has no fixture equivalent. No other gate test changes: the two
  scenario-naming delegates keep naming their scenarios and now delegate
  to the fixture test.

## Risks

- [A run-dependent value the substitution does not enumerate makes the pin
  flaky] → the failure is loud on the first differing run and the diff
  names the value; the substitution's docstring lists what it covers so a
  new value class is added deliberately.
- [An env var named `AGENTMARSHAL_UPDATE_GATE_FIXTURES` leaks into a
  caller's environment and silently rewrites fixtures] → the flag is read
  only in the pinned test, and its write lands in `tests/fixtures/` where
  `git status` shows it immediately.
- [The sidecar journal-only fixture reads as pinning a lane that does not
  exist] → the case is named for the candidate that would take the lane in
  an embedded journal, and the pinned refusal is what proves the lane is
  absent; design and the test docstring say so.
