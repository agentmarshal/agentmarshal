+++
schema = 2
id = "CR-146"
title = "The gate's default transcript is pinned by fixtures committed in the repository, not by a released binary"
scope = [
  "tests/",
  "openspec/changes/pin-gate-transcript-by-fixture/",
  "openspec/changes/archive/",
  "openspec/specs/gate-lanes/",
]
acceptance = [
  "the change pin-gate-transcript-by-fixture has a proposal, a design.md and a delta spec modifying the gate-lanes requirement 'A default run is unchanged' so that the transcript is compared with fixtures committed in the repository and any change to a fixture is made, and named, by the task that changes the output; every scenario in the delta is demonstrated by a test whose docstring names it; the change is archived with the archive command into openspec/specs/gate-lanes/",
  "fixtures under tests/ hold today's full transcript (stdout, stderr and exit status) of a default gate run for the implementation lane and the journal-only lane, each in the embedded and the sidecar placement, built the way the existing gate tests build their repositories; the test needs no external binary and runs in CI",
  "values that differ from run to run (commit hashes, temporary paths, record ids, times) are replaced by named placeholders through one documented substitution, so the comparison is exact everywhere else; on a mismatch the test shows a readable diff",
  "the comparison against a released 0.3.0 binary is removed, or kept only as an optional cross-check that cannot be the only pin; no other existing gate test is weakened",
  "the full CI sequence passes",
]
documents = ["openspec/specs/gate-lanes/"]
+++

# CR-146: the gate transcript pinned by fixtures

## Context

The gate-lanes requirement "A default run is unchanged" is pinned today by a
test that runs a released 0.3.0 binary and compares output byte for byte. It
is skipped wherever that binary is not installed, and once the journal
carries a record schema 0.3.0 cannot read (ADR-0022), the comparison becomes
impossible. Several 0.5.0 tasks will change the gate's output on purpose and
must name each change; others must show that they change nothing.

## Objective

The gate's default output is pinned by fixtures that run everywhere.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change to the gate's output or behaviour.
- Fixtures for lanes or modes other than those named in criterion 2.
