# project-settings Specification

## Purpose
How the project's `project.json` settings — the finding-class vocabulary,
the `changes_required` threshold and the agreement switch — are read, what
their defaults are, and how a malformed value is reported rather than
silently replaced.

## Requirements

### Requirement: the three settings are read in one place, with their defaults

The project settings are read by one reader returning a typed result:
`review.finding_classes`, `review.changes_required_threshold` and
`contract.require_agreement`. When a key is absent — including when its
whole section is absent — the reader SHALL return its default: the seven
finding classes `correctness`, `contract-mismatch`, `claim-accuracy`,
`scope`, `test-gap`, `security`, `style` for the vocabulary, `3` for the
threshold, and `false` for the agreement flag. Each key SHALL fall back
independently: a present key never changes what an absent one returns.

#### Scenario: a project with none of the keys gets every default
- **WHEN** `project.json` declares none of the three keys
- **THEN** the reader returns the seven-class vocabulary, the threshold 3
  and the agreement flag `false`

#### Scenario: an absent key falls back beside present ones
- **WHEN** `project.json` declares some of the three keys and not others
- **THEN** each declared key reads as declared and each absent key reads as
  its default

### Requirement: a present but malformed value is named, never silently replaced

A key that is present SHALL be validated, and a malformed value SHALL raise
an error naming the key and what it expects — never be replaced by the
default. Presence is decided by key membership: a key or section present
with the JSON value `null` is present, not absent. `review.finding_classes`
expects a non-empty list of distinct
non-empty strings without control characters; `other`, the fallback class
of the findings lifecycle, MAY be listed but is never required.
`review.changes_required_threshold` expects an integer of at least 1, and a
boolean is not an integer. `contract.require_agreement` expects a boolean.
A section holding a key SHALL be an object for the key to be read at all.

#### Scenario: a malformed vocabulary is named
- **WHEN** `review.finding_classes` is present and is not a non-empty list
  of distinct non-empty strings without control characters
- **THEN** reading the settings raises an error naming
  `review.finding_classes` and what it expects

#### Scenario: a malformed threshold is named
- **WHEN** `review.changes_required_threshold` is present and is not an
  integer of at least 1 — a boolean among the refused values
- **THEN** reading the settings raises an error naming
  `review.changes_required_threshold` and what it expects

#### Scenario: a malformed agreement flag is named
- **WHEN** `contract.require_agreement` is present and is not a boolean
- **THEN** reading the settings raises an error naming
  `contract.require_agreement` and what it expects

#### Scenario: a present null is malformed, not absent
- **WHEN** a key — or a section holding one — is present with the JSON
  value `null`
- **THEN** reading the settings raises an error naming the key and what
  it expects

#### Scenario: the fallback class may be listed
- **WHEN** `review.finding_classes` is a valid vocabulary that lists
  `other`
- **THEN** it is accepted as declared

#### Scenario: a section that is not an object is named
- **WHEN** a section holding one of the keys — `review` or `contract` — is
  present but is not an object
- **THEN** reading the settings raises an error naming the key that could
  not be read

### Requirement: doctor reports each malformed key as a failed check

`agentmarshal doctor` SHALL run one check per setting key, so each malformed
key is reported as a failed check naming the key and what it expects. A
project that declares none of the keys SHALL pass the checks. In a sidecar
the settings read are the journal repository's `project.json` — the one
the project lookup already finds — never the host's.

#### Scenario: a malformed key fails its own check
- **WHEN** doctor runs on a project with a malformed setting
- **THEN** that key's check fails, naming the key and what it expects

#### Scenario: several malformed keys each fail their own check
- **WHEN** doctor runs on a project with more than one malformed setting
- **THEN** each malformed key is reported by a failed check of its own

#### Scenario: a project with none of the keys passes
- **WHEN** doctor runs on a project that declares none of the three keys
- **THEN** the setting checks pass

#### Scenario: a sidecar reads the journal repository's settings
- **WHEN** doctor runs inside a sidecar journal repository
- **THEN** the setting checks read the journal repository's `project.json`
