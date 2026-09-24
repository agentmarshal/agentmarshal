## Purpose
What text a record or a contract header may carry. Its fields are rendered into
transcripts, briefs and prompts, so a value that can add a line to that output —
or make it read in an order its bytes do not have — is refused at the boundary
rather than escaped at the edge. The rule names the characters it refuses; a
printability test stood in for that and was stricter than the purpose, which
cost an adopter a journal an earlier release had accepted.

## ADDED Requirements

### Requirement: A record's text may not forge a line or reorder what is read
Text a record or a contract header carries is rendered into transcripts, briefs
and prompts. A value SHALL be refused when it contains a character of Unicode
category `Cc`, `Zl` or `Zp`, or a bidirectional control in U+202A–U+202E or
U+2066–U+2069: the first three can add a line, the last can make displayed text
read in an order its bytes do not have. Every other character SHALL be
accepted, space separators included. The refusal SHALL name the field it
refused.

#### Scenario: a newline in a finding id is refused
- **WHEN** a review record is written whose finding id contains a newline, a
  carriage return, U+2028 or U+2029
- **THEN** the write is refused and the message names the field

#### Scenario: a bidirectional override is refused
- **WHEN** a record value contains a character in U+202A–U+202E or
  U+2066–U+2069
- **THEN** the write is refused and the message names the field

#### Scenario: a space separator is accepted
- **WHEN** a value contains U+00A0, U+2007, U+2009 or U+202F and no refused
  character
- **THEN** the record is written, read and validated like any other

#### Scenario: a journal an earlier release accepted stays valid
- **WHEN** `agentmarshal validate` reads a review record written under an
  earlier schema whose finding id carries U+202F inside its text
- **THEN** the journal validates, and the task reports `OK`

#### Scenario: the rule holds the same on both sides
- **WHEN** the same refused character appears in a contract header entry
- **THEN** the contract is refused, by the same set of characters the record
  side refuses
