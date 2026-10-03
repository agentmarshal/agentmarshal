+++
schema = 2
id = "CR-151"
title = "project.json carries the finding-class vocabulary, the changes_required threshold and whether a contract needs agreement; doctor names a malformed value"
scope = [
  "src/agentmarshal/settings.py",
  "src/agentmarshal/doctor.py",
  "tests/",
  "openspec/changes/project-settings-0-5-0/",
  "openspec/changes/archive/",
  "openspec/specs/project-settings/",
]
acceptance = [
  "the change project-settings-0-5-0 has a proposal, a design.md and a delta spec adding the project-settings capability; every scenario in the delta spec is demonstrated by a test whose docstring names it; the change is archived with the archive command into openspec/specs/project-settings/",
  "one module (src/agentmarshal/settings.py) reads from project.json `review.finding_classes`, `review.changes_required_threshold` and `contract.require_agreement`, and returns the defaults when a key or its section is absent: the seven classes of ADR-0016 decision 3 (correctness, contract-mismatch, claim-accuracy, scope, test-gap, security, style), 3, and false",
  "a present but malformed value is never silently replaced by the default: the vocabulary must be a non-empty list of distinct non-empty strings without control characters (whether `other`, the fallback class, may be listed is decided in design.md), the threshold an integer of at least 1 (a boolean is not an integer), the agreement flag a boolean; reading a malformed value raises an error that names the key and what is expected",
  "`agentmarshal doctor` reports each malformed key as a failed check naming the key and what is expected, and a project with none of the keys passes as before; no other command reads the settings yet",
  "the full CI sequence passes",
]
documents = ["openspec/specs/project-settings/"]
+++

# CR-151: the 0.5.0 project settings

## Context

ADR-0022 section 6 adds three project.json keys: the finding-class
vocabulary of ADR-0016 decision 3, the `changes_required` threshold of
ADR-0016 decision 4 (default 3), and ADR-0018's switch that makes a
contract need an agreement (default false). Later tasks read them — the
review launcher, status, the gate. This task gives them one reader and lets
doctor say when a value is wrong.

## Objective

The three settings are read in one place, with their defaults, and a wrong
value is named rather than ignored.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any consumer of the settings (the launcher, status, the gate — later tasks).
- Writing the keys from `init`.
- Any other project.json key.
