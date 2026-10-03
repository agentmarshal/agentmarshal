## MODIFIED Requirements

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
