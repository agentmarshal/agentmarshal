## Purpose

What a task contract's header declares about who may implement the task,
who may review the result, and how independent the review must be — and what
that header refuses at the boundary. The header is parsed before anything it
names is trusted, so a malformed declaration is refused there with a message
naming the field, in the style of the schema-2 refusals, rather than read
loosely later.

## ADDED Requirements

### Requirement: Contract header schema 3 declares the assignment and the independence rules in force

A header with `schema = 3` MAY carry `implementers` and `reviewers`, each an
ordered list of non-empty actor ids — the order is the fallback order — and
`independence`, a list drawn from exactly `reviewer-not-writer`,
`distinct-actor`, `distinct-vendor` and `distinct-model`. Each of the three
fields is optional; absent, it SHALL parse as empty. The parsed header SHALL
expose the three fields, and a schema-3 header MAY carry every field a
schema-2 header carries.

#### Scenario: the assignment lists keep their declared order
- **WHEN** a schema-3 header lists `implementers` as `['devin', 'codex',
  'devin-ci']` and `independence` as `['reviewer-not-writer',
  'distinct-actor', 'distinct-vendor', 'distinct-model']`
- **THEN** the parsed header's `implementers` is `('devin', 'codex',
  'devin-ci')` and its `independence` is `('reviewer-not-writer',
  'distinct-actor', 'distinct-vendor', 'distinct-model')`

#### Scenario: each field is optional
- **WHEN** a schema-3 header carries none of `implementers`, `reviewers` and
  `independence`
- **THEN** it parses, and the parsed header's three fields are empty

#### Scenario: a schema-3 header may carry the schema-2 fields
- **WHEN** a schema-3 header carries `decisions`, `documents` or
  `extensions`
- **THEN** they parse as they do under schema 2

### Requirement: A header field requires the schema that introduced it

Any of `implementers`, `reviewers` and `independence` in a header of schema
1 or 2 SHALL be refused with a message naming the field and the schema it
requires, as the schema-2 fields are refused in a schema-1 header. A schema
version the header grammar does not know SHALL be refused — schema 4 is not
a contract header schema — and headers of schema 1 and 2 SHALL parse exactly
as before.

#### Scenario: a schema-3 field in an older header is refused
- **WHEN** a header of schema 1 or 2 carries `implementers`, `reviewers` or
  `independence`
- **THEN** it is refused with a message naming the field and that it
  requires schema 3

#### Scenario: an unknown schema version is refused
- **WHEN** a header declares `schema = 4`
- **THEN** it is refused as an unknown contract header schema

#### Scenario: headers of schema 1 and 2 parse exactly as before
- **WHEN** a header of schema 1 or 2 carries no schema-3 field
- **THEN** it parses as it did before, and the parsed header's three new
  fields are empty

### Requirement: A malformed schema-3 field is refused naming the field

A schema-3 assignment field is either absent or a non-empty list of distinct
non-empty strings: an empty list SHALL be refused naming the field, as SHALL
a repeated entry, an entry that is empty or not a string, and an entry
carrying a character the record side refuses — the rule the schema-2 string
fields pass. An `independence` entry outside the fixed vocabulary SHALL be
refused naming the rule.

#### Scenario: an empty list is refused naming the field
- **WHEN** a schema-3 header carries `implementers = []`
- **THEN** it is refused with a message naming `implementers`

#### Scenario: a repeated entry is refused naming the field
- **WHEN** a schema-3 header lists the same actor id twice in `reviewers`
- **THEN** it is refused with a message naming `reviewers`

#### Scenario: an empty actor id is refused naming the field
- **WHEN** a schema-3 header lists `implementers = ['devin', '']`
- **THEN** it is refused with a message naming `implementers`

#### Scenario: an entry that is not a string is refused naming the field
- **WHEN** a schema-3 header lists `implementers = ['devin', 42]`
- **THEN** it is refused with a message naming `implementers`

#### Scenario: an entry that could forge a line is refused
- **WHEN** an entry in `implementers`, `reviewers` or `independence`
  contains a character the record side refuses
- **THEN** it is refused as containing control characters

#### Scenario: an unknown independence rule is refused naming the rule
- **WHEN** a schema-3 header lists `independence = ['distinct-actor',
  'self-reviewed']`
- **THEN** it is refused with a message naming `self-reviewed`
