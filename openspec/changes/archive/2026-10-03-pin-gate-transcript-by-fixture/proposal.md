## Why

The requirement "A default run is unchanged" is pinned today by a test that
runs a released 0.3.0 binary and compares the transcript byte for byte. The
test is skipped wherever that binary is not installed — nothing installs it
in this repository's own CI — and once the journal carries a record schema
0.3.0 cannot read (ADR-0022) the comparison becomes impossible outright.
Several 0.5.0 tasks will change the gate's output on purpose and must name
each change; others must show that they change nothing. A pin that does not
run can do neither.

## What Changes

- The default run's transcript — stdout, stderr and exit status — is pinned
  by fixtures committed under `tests/fixtures/gate/`, one per lane and
  placement the pin covers: the implementation lane and the journal-only
  lane, each in the embedded and the sidecar placement.
- One substitution maps the values that differ from run to run — commit
  hashes, temporary paths, record ids, times — onto named placeholders, so
  the comparison is exact everywhere else. A mismatch fails showing a
  readable diff.
- A fixture is regenerated only when the test is explicitly asked to, so a
  task that changes the output on purpose regenerates it and the fixture's
  diff is part of that task's reviewed change.
- The byte-for-byte comparison against a released 0.3.0 binary is removed.
  The `released_030` helper stays: the schema tests in `test_findings.py`
  and `test_journal.py` use it for what the released version accepts, not
  for a transcript.

## Capabilities

- modified: `gate-lanes`

## Impact

- `tests/test_gate.py`, `tests/fixtures/gate/`.
- `openspec/specs/gate-lanes/spec.md` on archive.
- The scope-enforcement scenario "a candidate without renames prints the
  transcript it printed before" keeps its test, which now demonstrates the
  scenario through the committed fixture rather than the released binary.
