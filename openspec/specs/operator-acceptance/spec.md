# operator-acceptance Specification

## Purpose
How an operator's recorded decision to ship is carried by the journal and
read by its surfaces — an acceptance over a review's blocking findings
(ADR-0007) standing beside the two later forms (ADR-0013 decisions 5 and
17, ADR-0022 section 2): the acceptance of an extension pause, which raises
no review finding, and the acceptance of an operational CR, which has no
review at all — without one form ever being mistaken for another.

## Requirements

### Requirement: An acceptance record can accept an extension pause
From schema 7 an `acceptance` record SHALL be able to carry, in place of
`findings`, `accepted_pause` — an object carrying exactly the key
`extension`, whose value SHALL be a non-empty extension name that is one
path component: the rule an extension manifest applies to a name (not
empty, not `.` or `..`, carrying no `/` or `\`), and it SHALL pass the
forgeable-text rule. A pause acceptance SHALL bind by `accepted_commit`
only — one carrying `accepted_finding` SHALL be refused — and `accepted_by`
and `reason` SHALL be required as they are for an acceptance over findings.

#### Scenario: an acceptance of an extension pause is written and read back
- **WHEN** an `acceptance` record carries `accepted_pause` naming an
  extension, bound by `accepted_commit`, with `accepted_by` and `reason`
- **THEN** it is written and validated, and each field reads back as given

#### Scenario: an accepted_pause that is not exactly an extension object is refused
- **WHEN** `accepted_pause` is not an object, or is an object carrying keys
  other than `extension` alone
- **THEN** the record is refused and nothing is written

#### Scenario: an extension name that is not one non-empty path component is refused
- **WHEN** `extension` is not a string, is empty, is `.` or `..`, or
  carries `/` or `\`
- **THEN** the record is refused and nothing is written

#### Scenario: an extension name that could forge a line is refused
- **WHEN** `extension` carries a character that could add a line to
  rendered output or reorder it
- **THEN** the record is refused

#### Scenario: a pause acceptance bound to a finding is refused
- **WHEN** an `acceptance` record carries `accepted_pause` with
  `accepted_finding`
- **THEN** it is refused and nothing is written

### Requirement: An acceptance record can accept an operational CR
From schema 7 an `acceptance` record SHALL be able to carry, in place of
`findings`, `operational` with the value `true` — the acceptance of an
operational CR, which has no review at all. `operational` carrying any
value but `true` SHALL be refused. An operational acceptance SHALL bind by
`accepted_commit` only — one carrying `accepted_finding` SHALL be refused —
and `accepted_by` and `reason` SHALL be required as they are for an
acceptance over findings.

#### Scenario: an acceptance of an operational CR is written and read back
- **WHEN** an `acceptance` record carries `operational: true`, bound by
  `accepted_commit`, with `accepted_by` and `reason`
- **THEN** it is written and validated, and each field reads back as given

#### Scenario: an operational value other than true is refused
- **WHEN** an `acceptance` record's `operational` carries `false`, a
  string, a number or any other value but `true`
- **THEN** it is refused and nothing is written

#### Scenario: an operational acceptance bound to a finding is refused
- **WHEN** an `acceptance` record carries `operational` with
  `accepted_finding`
- **THEN** it is refused and nothing is written

### Requirement: An acceptance names exactly one of its forms
An `acceptance` record SHALL carry exactly one of `findings`,
`accepted_pause` and `operational`; a record carrying more or fewer SHALL
be refused with a refusal naming the three. The findings form SHALL keep
its validation: `findings` is a non-empty array of unique non-empty finding
ids, each passing the forgeable-text rule.

#### Scenario: a record carrying more or fewer than exactly one form is refused
- **WHEN** an `acceptance` record carries none of `findings`,
  `accepted_pause` and `operational`, or more than one of them
- **THEN** it is refused with a refusal naming the three, and nothing is
  written

#### Scenario: an acceptance over findings keeps its validation
- **WHEN** an `acceptance` record carrying `findings` has an empty or
  non-array `findings`, duplicate ids, an empty id or an id that could
  forge a line
- **THEN** it is refused as before, and nothing is written

### Requirement: The new forms are fields of schema 7
An `acceptance` record carrying `accepted_pause` or `operational` below
schema 7 SHALL be refused at write and on read — the fields are admitted
only from schema 7, registered as a schema-7 field family of the
`acceptance` record type through the record-type and field registrations
the other schema-7 fields use, not by a second mechanism. A writer SHALL
stamp 7 through the minimum-schema derivation; an acceptance carrying
`findings` SHALL be validated and stamped exactly as before.

#### Scenario: a writer stamps 7 for an acceptance carrying a new form
- **WHEN** an acceptance record is built carrying `accepted_pause` or
  `operational`
- **THEN** it carries schema 7

#### Scenario: an acceptance carrying a new form below schema 7 is refused at write
- **WHEN** an `acceptance` record stamped below 7 carries `accepted_pause`
  or `operational`
- **THEN** it is refused and nothing is written

#### Scenario: an acceptance carrying a new form below schema 7 is refused on read
- **WHEN** the journal holds an `acceptance` record stamped below 7 that
  carries `accepted_pause` or `operational`
- **THEN** reading the task's records refuses it

#### Scenario: an acceptance over findings keeps its stamp
- **WHEN** an acceptance record is built carrying `findings`
- **THEN** it carries the schema it carried before the new forms existed

### Requirement: Readers keep acceptance over findings to the acceptances that carry findings
No reader SHALL treat a pause or operational acceptance as an acceptance
over findings, and none SHALL fail on an acceptance without `findings`.
The gate SHALL judge acceptance over findings by the latest acceptance of
that commit or finding that carries `findings`, on either binding — a
pause or operational acceptance written later does not shadow it. `status`
SHALL print a line for each new form naming `accepted_pause=<extension>`
or `operational` where an acceptance over findings names its findings,
with the same binding and self-acceptance marking. `report` SHALL derive
`accepted-over-findings` only from an acceptance carrying `findings`.
Every output for an acceptance carrying `findings` — the gate transcripts,
the `status` lines and the `report` line — SHALL be unchanged byte for
byte; the `accept` command writes the new forms, and nothing else SHALL
act on them.

#### Scenario: a pause acceptance does not shadow an acceptance over findings
- **WHEN** an acceptance carrying `findings` stands on a commit and a pause
  or operational acceptance bound to the same commit is written later
- **THEN** the gate judges the findings acceptance and reports the accepted
  over findings line, on the commit binding as on the finding binding

#### Scenario: an acceptance without findings is not judged as one
- **WHEN** the latest acceptance bound to the candidate carries no
  `findings`
- **THEN** the gate does not report an acceptance over findings

#### Scenario: status prints a pause acceptance
- **WHEN** a task holds a pause acceptance
- **THEN** its record line names `accepted_pause=<extension>` where an
  acceptance over findings names its findings, and the summary and
  self-acceptance marking apply as for an `accepted_commit` acceptance

#### Scenario: status prints an operational acceptance
- **WHEN** a task holds an operational acceptance
- **THEN** its record line names `operational` where an acceptance over
  findings names its findings, and the summary and self-acceptance marking
  apply as for an `accepted_commit` acceptance

#### Scenario: report derives accepted-over-findings only from an acceptance carrying findings
- **WHEN** a task's acceptances carry `accepted_pause` or `operational`
  and none carries `findings`
- **THEN** its report line derives no `accepted-over-findings` decision

#### Scenario: every output for an acceptance over findings is unchanged
- **WHEN** an acceptance carries `findings`
- **THEN** the gate transcripts, the `status` lines and the `report` line
  are byte-identical to what they were before the new forms existed

### Requirement: `accept --pause` records an acceptance of an extension's pause

`agentmarshal accept --task <id> --commit <rev> --pause <extension>
--by <party> --reason <text>` SHALL write one `acceptance` record
through `create_acceptance_record`'s `accepted_pause` parameter —
carrying `accepted_pause` naming `<extension>` and no `findings` —
bound by `accepted_commit` to the commit `--commit` resolves to, with
`accepted_by` and `reason` as the flags give them (ADR-0013 decision
5; ADR-0022 section 2). The commit SHALL be resolved —
`git rev-parse --verify <rev>^{commit}` — in the journal's
repository: the repository that holds the journal in either
placement, so a sidecar records against the commits its own
repository carries, and a reference that does not resolve to a
commit there SHALL be refused naming it. `<extension>` SHALL name a
shared extension the journal repository's working tree declares —
the manifest read through `read_extension_manifest`,
`.agentmarshal/extensions/<name>.toml` or
`.agentmarshal/extensions/<name>/manifest.toml`, the file form or
the directory form — and a name no manifest declares and a manifest
that cannot be read SHALL each refuse the write naming the
extension. The task SHALL be one an `acceptance` record may be
written for — the lifecycle admission an acceptance over findings
gets — and the task's reviews SHALL NOT be consulted: a pause
raises no review finding, so the review state neither permits nor
refuses. Every refusal SHALL write nothing.

#### Scenario: a pause acceptance is written for a declared extension at the resolved commit
- **WHEN** `accept --pause` runs on an open task naming a shared
  extension the working tree declares, with `--commit` naming a
  commit the journal's repository holds
- **THEN** one acceptance record is written carrying
  `accepted_pause` for that extension and no `findings`, bound by
  `accepted_commit` to the full 40-hex id the reference resolves to,
  and the command prints the record's path

#### Scenario: a pause acceptance is written where no review stands
- **WHEN** `accept --pause` runs on an open task whose latest review
  is approved, or which carries no review at all — a pause raises no
  review finding, so the review state is not consulted
- **THEN** the acceptance is written

#### Scenario: a short or symbolic --commit resolves to the full id
- **WHEN** `--commit` names a reference that is not 40 hex — a short
  id, a branch, `HEAD`
- **THEN** the record's `accepted_commit` is the full 40-hex id the
  reference resolves to in the journal's repository

#### Scenario: a commit that does not resolve is refused writing nothing
- **WHEN** `--commit` names a reference the journal's repository does
  not hold
- **THEN** it is refused naming the reference, and no record is
  written

#### Scenario: an extension no shared manifest declares is refused naming it
- **WHEN** `--pause` names an extension with no manifest in either
  form in the journal repository's working tree
- **THEN** the write is refused naming the extension, and no record
  is written

#### Scenario: an extension whose manifest cannot be read is refused naming it
- **WHEN** `--pause` names an extension whose manifest exists but
  cannot be read
- **THEN** the write is refused naming the extension, and no record
  is written

#### Scenario: an extension declared in the directory form is accepted
- **WHEN** `--pause` names an extension whose manifest lives at
  `<name>/manifest.toml` — the directory form
- **THEN** the acceptance is written carrying `accepted_pause` for
  that extension

#### Scenario: a task that admits no acceptance is refused writing nothing
- **WHEN** `accept --pause` runs on a task that has completed or been
  abandoned
- **THEN** it is refused naming the state, and no record is written

### Requirement: `accept --operational` records an acceptance of an operational CR

`agentmarshal accept --task <id> --commit <rev> --operational --by
<party> --reason <text>` SHALL write one `acceptance` record through
`create_acceptance_record`'s `operational` parameter — carrying
`operational: true` and no `findings` — bound by `accepted_commit`
to the commit `--commit` resolves to, resolved in the journal's
repository as under `accept --pause`, with `accepted_by` and
`reason` as the flags give them (ADR-0013 decision 17; ADR-0022
section 2). An operational CR carries no review at all, so the task
SHALL NOT be required to have one; the task SHALL be one an
`acceptance` record may be written for, as for the other forms. A
`--commit` that does not resolve SHALL be refused naming it; every
refusal SHALL write nothing.

#### Scenario: an operational acceptance is written at the resolved commit
- **WHEN** `accept --operational` runs on an open task that carries
  no review — an operational CR has none — with `--commit` naming a
  commit the journal's repository holds
- **THEN** one acceptance record is written carrying
  `operational: true` and no `findings`, bound by `accepted_commit`
  to the resolved commit, and the command prints the record's path

#### Scenario: an operational --commit that does not resolve is refused writing nothing
- **WHEN** `accept --operational` runs with `--commit` naming a
  reference the journal's repository does not hold
- **THEN** it is refused naming the reference, and no record is
  written

#### Scenario: a task that admits no acceptance refuses an operational write
- **WHEN** `accept --operational` runs on a task that has completed
  or been abandoned
- **THEN** it is refused naming the state, and no record is written

### Requirement: `accept` keeps its three forms mutually exclusive

The three acceptance forms — over a review's blocking findings,
`--pause` and `--operational` — SHALL be mutually exclusive on the
command and exactly one SHALL apply: naming neither new flag selects
the findings form, as today. `--pause` and `--operational` SHALL
refuse each other naming the flags, and `--finding` and
`--accepted-finding` — which belong to the findings form — SHALL be
refused with `--pause` or `--operational`, the refusal naming the
flags. Each refusal SHALL write nothing. Acceptance over findings
SHALL behave exactly as it does today: the same binding rule, the
same review checks, the same record.

#### Scenario: --pause and --operational together are refused naming the flags
- **WHEN** `accept` is invoked with `--pause` and `--operational`
  together
- **THEN** it is refused naming the two flags, and no record is
  written

#### Scenario: --accepted-finding is refused with --pause or --operational naming the flags
- **WHEN** `accept` is invoked with `--accepted-finding` and `--pause`
  or `--operational`
- **THEN** it is refused naming the flags, and no record is written

#### Scenario: --finding is refused with --pause or --operational naming the flags
- **WHEN** `accept` is invoked with `--finding` and `--pause` or
  `--operational`
- **THEN** it is refused naming the flags, and no record is written

#### Scenario: an acceptance over findings is unchanged
- **WHEN** `accept` is invoked with neither `--pause` nor
  `--operational`
- **THEN** it behaves exactly as before the new forms existed: the
  latest non-approving review of the exact binding is required, its
  blocking findings are the record's, and its refusals are unchanged
