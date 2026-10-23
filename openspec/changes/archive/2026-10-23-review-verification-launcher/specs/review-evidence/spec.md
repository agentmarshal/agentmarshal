## ADDED Requirements

### Requirement: The verdict may carry what the reviewer ran and read, and the evidence behind its findings

The verdict protocol SHALL admit an optional `verification` object —
what the reviewer ran and with what result, what it checked by reading
only, and what it could not run and why (ADR-0017 decision 4):
`executed`, a list of `{what, result}` objects; `read`, a list of
strings; `not_run`, a list of `{what, why}` objects — and an optional
`evidence` object mapping finding ids to the evidence behind each
(ADR-0017 decision 5): a link, a `file:line`, or the command that
checked the claim with the essential part of its output. The prompt the
launcher builds SHALL ask, for either binding, for the `verification`
sections and for evidence per finding id, and SHALL state that a finding
about an external fact the reviewer could not check is advisory —
marked "unconfirmed". The commit prompt SHALL additionally ask that the
prose name, for each acceptance criterion, where the diff meets it and
which test demonstrates it.

#### Scenario: a verification object is admitted by the protocol
- **WHEN** a verdict carries `verification` naming `executed`, `read`
  and `not_run` sections
- **THEN** the verdict parses — `verification` is an optional key,
  never an unknown one

#### Scenario: an evidence object is admitted by the protocol
- **WHEN** a verdict carries `evidence` mapping finding ids to evidence
  references
- **THEN** the verdict parses — `evidence` is an optional key, never an
  unknown one

#### Scenario: the prompt asks for the sections and states the unconfirmed rule
- **WHEN** the launcher builds the review prompt for a commit
- **THEN** it asks for a `verification` object with the `executed`,
  `read` and `not_run` sections, asks for `evidence` per finding id, and
  states that a finding about an external fact the reviewer could not
  check is advisory — marked "unconfirmed"

#### Scenario: the commit prompt asks where each criterion is met
- **WHEN** the launcher builds the review prompt for a commit
- **THEN** it asks that the prose name, for each acceptance criterion,
  where the diff meets it and which test demonstrates it

#### Scenario: the finding prompt asks for the same sections
- **WHEN** the launcher builds the review prompt for a finding
- **THEN** it asks for `verification` and `evidence` and states that a
  finding about an external fact the reviewer could not check is
  advisory — marked "unconfirmed"

### Requirement: The launcher records the verification a verdict names, dropping what it cannot keep

When a launched review's verdict carries `verification`, the record
SHALL carry each section and entry the record rules admit. A key outside
`executed`, `read` and `not_run` SHALL be dropped with a warning naming
it; a section that is not a non-empty array SHALL be dropped with a
warning naming it; an entry the record rules would refuse SHALL be
dropped with a warning naming the section and the position, and the
section's surviving entries are recorded. A section left with no usable
entry SHALL land nothing, and a `verification` that is not an object
SHALL be dropped as a whole with a warning. A verdict SHALL NOT be
refused over `verification`: the run is paid and the sections are the
reviewer's declaration (ADR-0017 decision 4). A verdict carrying no
`verification` SHALL be recorded exactly as before — no `verification`
field.

#### Scenario: the verification sections are recorded
- **WHEN** a verdict carries `verification` naming `executed`, `read`
  and `not_run` entries the record rules admit
- **THEN** the record carries them, and the review stamps schema 7

#### Scenario: a section outside the three is dropped with a warning
- **WHEN** a verdict's `verification` carries a key that is not
  `executed`, `read` or `not_run`
- **THEN** the key is dropped with a warning naming it and the admitted
  sections are recorded

#### Scenario: a section that is not a non-empty array is dropped with a warning
- **WHEN** a verdict's `verification` carries `executed`, `read` or
  `not_run` as an empty array or a value that is not an array
- **THEN** the section is dropped with a warning naming it and the other
  sections are recorded

#### Scenario: a malformed verification entry is dropped with a warning
- **WHEN** a verdict's `verification` section carries an entry the
  record rules would refuse — a `read` item or an `executed`/`not_run`
  entry that is not of the admitted shape, or a string inside that is
  empty or could forge a line
- **THEN** the entry is dropped with a warning naming the section and
  the position, and the section's surviving entries are recorded

#### Scenario: a section with no usable entry lands nothing
- **WHEN** every entry of a verdict's `verification` section is dropped
- **THEN** that section does not land — and a `verification` whose
  sections all dropped writes no `verification` field

#### Scenario: a verification that is not an object is dropped whole with a warning
- **WHEN** a verdict's `verification` is not an object
- **THEN** the verdict is recorded, no `verification` field lands and a
  warning says the value was dropped

#### Scenario: an empty verification object is dropped with a warning
- **WHEN** a verdict's `verification` is an empty object
- **THEN** no `verification` field lands and a warning says nothing was
  recorded

#### Scenario: a verdict without verification records exactly as before
- **WHEN** a verdict carries no `verification`
- **THEN** the record carries no `verification` field

### Requirement: The launcher records the evidence a verdict names, dropping what it cannot keep

When a launched review's verdict carries `evidence`, the record SHALL
carry each entry whose key is an id among the verdict's `findings` or
`advisory_findings` and whose value is a usable evidence string — a
non-empty string carrying no character the forgeable-text rule refuses.
An entry for an id the verdict does not carry SHALL be dropped with a
warning naming the id, and an entry whose value the record could not
hold SHALL be dropped with a warning naming the id — the entries that
remain are recorded. An `evidence` that is not an object SHALL be
dropped as a whole with a warning. A verdict SHALL NOT be refused over
`evidence`: the run is paid and the reference is the reviewer's
declaration (ADR-0017 decision 5). A verdict carrying no `evidence`
SHALL be recorded exactly as before — no `evidence` field.

#### Scenario: evidence for the verdict's ids is recorded
- **WHEN** a verdict carries `evidence` mapping ids among its `findings`
  and `advisory_findings` to usable reference strings
- **THEN** the record carries them, and the review stamps schema 7

#### Scenario: an evidence entry for an id the verdict does not carry is dropped with a warning
- **WHEN** a verdict's `evidence` names an id that is not among its
  `findings` or `advisory_findings`
- **THEN** that entry is dropped with a warning naming the id and the
  entries for the verdict's ids are recorded

#### Scenario: an evidence entry the record could not hold is dropped with a warning
- **WHEN** a verdict's `evidence` entry carries a value that is not a
  non-empty string, or one that could forge a line
- **THEN** the entry is dropped with a warning naming the id and the
  remaining entries are recorded

#### Scenario: an evidence that is not an object is dropped whole with a warning
- **WHEN** a verdict's `evidence` is not an object
- **THEN** the verdict is recorded, no `evidence` field lands and a
  warning says the value was dropped

#### Scenario: an empty evidence object is dropped with a warning
- **WHEN** a verdict's `evidence` is an empty object
- **THEN** no `evidence` field lands and a warning says nothing was
  recorded

#### Scenario: a verdict without evidence records exactly as before
- **WHEN** a verdict carries no `evidence`
- **THEN** the record carries no `evidence` field

## MODIFIED Requirements

### Requirement: Without --actor the review paths are unchanged

Without `--actor` both paths SHALL write the same record, stamp the same
schema and print the same lines as before the flag existed — apart from
the `previous_review` link, the `classes` and the `verification` and
`evidence` a launched review records of its own, which are the
launcher's and not the flag's: the flag adds a capability, never an
obligation.

#### Scenario: a review written without --actor is byte-for-byte as before
- **WHEN** `submit-review` or `review` records a verdict without
  `--actor`
- **THEN** the record — apart from its id and times — is byte-for-byte
  the record the command wrote before the flag existed, less the
  `previous_review`, `classes`, `verification` and `evidence` a launched
  review records regardless of the flag, and every line the command
  prints is unchanged
