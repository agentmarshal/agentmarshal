## ADDED Requirements

### Requirement: record-session writes the schema-7 session fields from flags
`agentmarshal record-session` SHALL accept, each optional,
`--commit <rev>`, `--model <name>`, `--trace <link>`,
`--cli-session <id>`, `--report-ready` and `--fallback-reason <text>`,
writing the matching field of the schema-7 session family — `commit`,
`model`, `trace`, `cli_session`, `report_ready` and `fallback_reason`.
A session recorded with any of them SHALL be stamped schema 7, as any
record carrying the family is; a session recorded with none of them
SHALL keep the schema it had. A flag value the record rules refuse —
an empty or whitespace-only string, a forgeable character — SHALL be
refused with the record rule's message and no record SHALL be written.
`--outcome` SHALL remain free text, unconstrained by the flags.

#### Scenario: a session recorded with the flags carries the fields
- **WHEN** `record-session` runs with `--commit`, `--model`, `--trace`,
  `--cli-session`, `--report-ready` and `--fallback-reason`
- **THEN** the record is written, and each matching field reads back as
  given

#### Scenario: the flags are optional
- **WHEN** `record-session` runs with none of the family's flags
- **THEN** the record is written and carries none of the family's
  fields

#### Scenario: a session recorded with a flag is stamped schema 7
- **WHEN** `record-session` runs with any of the family's flags
- **THEN** the record carries schema 7

#### Scenario: a session recorded without the flags keeps its schema
- **WHEN** `record-session` runs with none of the family's flags
- **THEN** the record carries the schema it carried before the flags
  existed — 3, or 6 for a `coordination` activity

#### Scenario: a refused flag value writes nothing
- **WHEN** a flag carries a value the record rules refuse — an empty or
  whitespace-only string, or a character that could forge a rendered
  line
- **THEN** the command refuses with the record rule's message and
  writes no record

#### Scenario: an outcome of free text is still recorded
- **WHEN** `--outcome` carries free text
- **THEN** it is recorded as given

### Requirement: --commit resolves in the repository the work is in
`--commit` SHALL accept any revision git accepts, resolved with
`git rev-parse --verify <rev>^{commit}` in the repository the work is in
— the project's own repository for an embedded journal, the host
repository for a sidecar — and the record SHALL carry the resolved
full 40-character id. A revision git cannot resolve SHALL be refused
with a message naming it, and no record SHALL be written.

#### Scenario: a revision resolves to the full commit id
- **WHEN** `record-session --commit` names a revision that resolves in
  the repository the work is in
- **THEN** the record's `commit` is the full 40-character id it
  resolves to

#### Scenario: in a sidecar the revision resolves in the host
- **WHEN** `record-session --commit` runs in a sidecar naming a
  revision only the host knows
- **THEN** the record's `commit` is the id the host resolves it to

#### Scenario: an unknown revision is refused naming it
- **WHEN** `--commit` names a revision git cannot resolve
- **THEN** the command refuses with a message naming the revision and
  writes no record
