## ADDED Requirements

### Requirement: A review record may name the contract it judged
A review record MAY carry `reviewed_contract`: the sha256, in lowercase hex, of
the contract text the reviewer was handed. A record carrying it SHALL declare a
schema that allows it; a record without it SHALL be valid under the schema it
declares, and its absence SHALL never be reported anywhere.

#### Scenario: the launcher records the contract it handed over
- **WHEN** `agentmarshal review` records a verdict
- **THEN** the review record carries `reviewed_contract`, the sha256 of the
  exact contract bytes the prompt carried

#### Scenario: the human path records no contract
- **WHEN** `agentmarshal submit-review` records a verdict
- **THEN** the record carries no `reviewed_contract`, because no contract was
  handed to anyone, and the record is valid without it

#### Scenario: the field requires the schema that allows it
- **WHEN** a record carrying `reviewed_contract` declares a schema written
  before the field existed
- **THEN** the record is refused, with a message naming the field and the schema
  it requires

#### Scenario: records written before the field are read as they were
- **WHEN** a journal holds review records written under earlier schemas
- **THEN** every command reads them as it did before this change
