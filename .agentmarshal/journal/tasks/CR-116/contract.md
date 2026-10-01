+++
schema = 1
id = "CR-116"
title = "The default branch carries 0.5.0.dev0 again, and the 0.4.1 notes read precisely"
scope = [
  "pyproject.toml",
  "uv.lock",
  "src/agentmarshal/__init__.py",
  "tests/test_smoke.py",
  "UPGRADING.md",
  "openspec/changes/archive/2026-09-24-narrow-the-forgeable-text-rule/design.md",
]
acceptance = [
  "the package version is 0.5.0.dev0 in pyproject.toml, src/agentmarshal/__init__.py and uv.lock, the smoke test asserts it, and `agentmarshal --version` prints it",
  "UPGRADING.md's paragraph telling a 0.3.0 installation to go straight to 0.4.1 names the section it refers to by its heading (0.3.0 -> 0.4.0) rather than by position, and says that where that section asks to verify the installed version is 0.4.0, such an installation verifies 0.4.1",
  "the archived CR-114 design.md says that extensions.py reaches the shared predicate through contracts.py's reject_control_characters wrapper, which is what its import does; no other sentence of that document changes",
  "no statement about 0.4.0 or 0.4.1 as history changes beyond the two above, and the full CI sequence passes",
]
+++

# CR-116: the default branch carries 0.5.0.dev0 again

## Context

0.4.1 was tagged on 2026-09-24 from a branch that the release task set to
0.4.1. CONTRIBUTING says the first task after a tag sets a `.dev0` version
again; until it lands, anything built from the default branch reports the
published version, which is the confusion the `.dev0` rule exists to prevent.

The last review round of the release task (CR-115) left two advisory findings,
raised by both runs, about the paragraph that sends a 0.3.0 installation
straight to 0.4.1: it points at "the section below it", which is not the next
section in the file, and it leaves the reader of the 0.3.0 -> 0.4.0 section
verifying `--version` against 0.4.0. CR-114 left one: its design document says
`extensions.py` reaches the record predicate "through its own name", while the
module imports the contracts-side wrapper.

## Objective

Builds from the default branch say they are development builds again, and the
two release notes a 0.3.0 adopter reads send them to the right place with the
right version to check.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change in behaviour.
- Any other edit to the 0.3.0 -> 0.4.0 section: it is history, written for 0.4.0.
- CHANGELOG.md: it describes published releases, and nothing here is published.
