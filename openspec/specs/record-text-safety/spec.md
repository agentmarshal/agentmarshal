# record-text-safety Specification

## Purpose
What text a record or a contract header may carry. Its fields are rendered into
transcripts, briefs and prompts, so a value that can add a line to that output —
or make it read in an order its bytes do not have — is refused at the boundary
rather than escaped at the edge. The rule names the characters it refuses; a
printability test stood in for that and was stricter than the purpose, which
cost an adopter a journal an earlier release had accepted.

## Requirements

### Requirement: A record's text may not forge a line or reorder what is read
Where this rule is applied — a review record's finding and advisory finding
ids, an acceptance record's fields and finding ids, a finding record's summary
and artifact references, a review artifact's pinned reference, an artifact's or
an extension's name, a contract header's `documents`, `decisions` and
`extensions` entries, and an extension manifest's footprint entries — the value
is rendered into transcripts, briefs and prompts. Such a value SHALL be refused
at write time when it contains a character of Unicode
category `Cc`, `Cs`, `Zl` or `Zp`, or a bidirectional mark, embedding, override
or isolate — U+061C, U+200E, U+200F, U+202A–U+202E, U+2066–U+2069. `Cc`, `Zl`
and `Zp` can add a line; the bidirectional characters can make displayed text
read in an order its bytes do not have; an unpaired surrogate (`Cs`) cannot be
encoded as UTF-8, so a record carrying one could not be written back out. Every
other character SHALL be accepted, space separators and private-use codepoints
included. The refusal SHALL name the field it refused. A record that carries
such a character anyway — one a later read rule does not reach — SHALL be
escaped where the tool displays it rather than refused.

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

### Requirement: A refused character a record still carries is escaped on display
At read time a record is checked by the rules of its own schema, so a value a
later rule would refuse at write can still be read — one written before the
rule existed, or one written around the writer with a lowered schema. Where
the tool renders a value taken from a record or a contract — `agentmarshal
status` and `agentmarshal report`, the gate's transcript, the brief and the
reviewer prompt — every refused character SHALL print as a visible escape:
`\n`, `\r` and `\t` by name, `\uXXXX` for the rest of the Basic Multilingual
Plane, `\UXXXXXXXX` past it. Every other character SHALL print as it is, so
a record carrying no refused character renders byte-identically. The escaped
set SHALL be the set the write rule refuses — one predicate decides both —
and escaping applies to text taken from a record or a contract, never to the
tool's own fixed text. Material the tool presents as a block of its own — a
contract document inlined into a brief or a prompt, a diff, an artifact's
embedded content — is not a value placed into a line and is shown as it
stands; within the amendment history a reason's real newlines remain its
quoting's line structure while every other refused character prints as its
escape.

#### Scenario: a refused character prints escaped in status
- **WHEN** `agentmarshal status` renders a record field or a contract value
  carrying a newline or a bidirectional override — a value today's read rules
  would refuse on disk
- **THEN** each refused character prints as its escape and stays on the line
  it belongs to

#### Scenario: a refused character prints escaped in report
- **WHEN** `agentmarshal report` renders a value carrying a refused character
- **THEN** each refused character prints as its escape on the value's own
  line

#### Scenario: a refused character prints escaped in the gate's transcript
- **WHEN** the gate's transcript renders a value taken from a record or a
  contract — a finding id, an acceptance field, a reviewer name, an artifact
  reference, a scope entry — carrying a newline or a bidirectional override
- **THEN** each refused character prints as its escape on the line that
  carries it

#### Scenario: a refused character prints escaped in the brief
- **WHEN** `agentmarshal brief` renders a value taken from a record or a
  contract — a scope or acceptance entry, an amendment's fields, a named
  document or decision — carrying a refused character
- **THEN** each refused character prints as its escape where the value joins
  a line

#### Scenario: a refused character prints escaped in the reviewer prompt
- **WHEN** the reviewer prompt renders a value taken from a record or a
  contract — a finding's id, claim summary or artifact references, the named
  contract material, the amendment history — carrying a refused character
- **THEN** each refused character prints as its escape where the value joins
  a line

#### Scenario: what the write refuses, the display escapes
- **WHEN** a character the forgeable-text rule refuses reaches a renderer
- **THEN** it prints as `\n`, `\r`, `\t` or its `\uXXXX` (`\UXXXXXXXX`) escape,
  and every character the rule accepts prints as it is

#### Scenario: a value without refused characters prints as it is
- **WHEN** `agentmarshal status`, `agentmarshal report`, `agentmarshal brief`,
  the gate or the reviewer prompt renders records carrying no refused
  character
- **THEN** the output is byte-identical to what it was before escaping

### Requirement: The gate escapes every value it did not write itself
A candidate's file names are record text no rule reaches: they are legal
in git and the gate reads them raw. Where the gate renders a value it did
not write — a candidate path the change set names, a rename's source or
target, a record path, an extension or manifest path, or a value carried
into an error or refusal message, an exception's text, a ref and git's
own error output included — every refused character SHALL print as its
escape: `\n`, `\r` and `\t` by name, `\uXXXX` (`\UXXXXXXXX` past the
Basic Multilingual Plane) for the rest, the same characters and forms the
display-escape rule uses, so nothing a candidate controls can add a line
to what the gate prints or make it read in an order its bytes do not
have. A value carrying no refused character SHALL print byte-identically.

#### Scenario: a candidate path that would forge a line is named in escaped form
- **WHEN** a candidate's change set names a path carrying a newline or a
  bidirectional override and the gate names it — on the scope line or a
  record-collision line
- **THEN** each refused character prints as its escape on the line that
  names it, and no line the name would have forged appears

#### Scenario: a rename's source or target carrying a refused character is named in escaped form
- **WHEN** a rename's source or target carries a refused character and
  the gate names it among the paths outside contract scope
- **THEN** it prints escaped on the line that names it

#### Scenario: a path whose bytes are not UTF-8 is named in escaped form
- **WHEN** a path a gate listing returns carries bytes that are not UTF-8
  and the gate names it
- **THEN** the undecodable bytes print in escaped form on the line that
  names it, and the run is not refused on the name's account

#### Scenario: a refusal names a forgeable value in escaped form
- **WHEN** an error or refusal message embeds a value taken from the
  candidate, the journal or git output — a ref, a path, an exception's
  text — that carries a refused character
- **THEN** the message prints the value escaped and stays the one line it
  was

#### Scenario: a candidate whose values carry no refused character prints as before
- **WHEN** every path and value the gate renders carries no refused
  character
- **THEN** the transcript and its refusals are byte-identical to what
  they were
