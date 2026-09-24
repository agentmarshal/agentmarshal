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
category `Cc`, `Cs`, `Zl` or `Zp`, or a bidirectional mark, embedding, override
or isolate — U+061C, U+200E, U+200F, U+202A–U+202E, U+2066–U+2069. `Cc`, `Zl`
and `Zp` can add a line; the bidirectional characters can make displayed text
read in an order its bytes do not have; an unpaired surrogate (`Cs`) cannot be
encoded as UTF-8, so a record carrying one could not be written back out. Every
other character SHALL be accepted, space separators and private-use codepoints
included. The refusal SHALL name the field it refused.

#### Scenario: a newline in a finding id is refused
- **WHEN** a review record is written whose finding id contains a newline, a
  carriage return, U+2028 or U+2029
- **THEN** the write is refused and the message names the field

#### Scenario: a bidirectional override is refused
- **WHEN** a record value contains a bidirectional mark, embedding, override or
  isolate
- **THEN** the write is refused and the message names the field

#### Scenario: an unpaired surrogate is refused
- **WHEN** a record value contains an unpaired surrogate
- **THEN** the write is refused, because the value could not be written back as
  UTF-8

#### Scenario: a space separator is accepted
- **WHEN** a value contains U+00A0, U+2007, U+2009 or U+202F and no refused
  character
- **THEN** the record is written, read and validated like any other

#### Scenario: the rule guards every place that renders record text
- **WHEN** a review record's artifact reference carries a refused character
- **THEN** `agentmarshal validate` reports it, by the same set of characters the
  writer refuses

#### Scenario: a journal an earlier release accepted stays valid
- **WHEN** `agentmarshal validate` reads a review record written under an
  earlier schema whose finding id carries U+202F inside its text
- **THEN** the journal validates, and the task reports `OK`

#### Scenario: the rule holds the same on both sides
- **WHEN** the same refused character appears in a contract header entry
- **THEN** the contract is refused, by the same set of characters the record
  side refuses
