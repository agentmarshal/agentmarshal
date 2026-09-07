## ADDED Requirements

### Requirement: A candidate's change set names every path it touches
The gate SHALL derive the set of paths a candidate changes from one listing in
which a rename contributes its source as a deletion and its destination as an
addition, and a copy contributes its destination as an addition. Every check
that reads the candidate's paths — the scope check, the choice between the
journal-only and diff lanes, and the refusal of an empty range — SHALL read
that set.

#### Scenario: a rename out of scope is refused
- **WHEN** a candidate renames a path the contract's scope does not cover to a
  path it does cover
- **THEN** the gate refuses the candidate and the scope line names the source
  path among the paths outside contract scope

#### Scenario: a rename within scope passes
- **WHEN** a candidate renames a path within the contract's scope to another
  path within it
- **THEN** the scope line passes with the wording it had before

#### Scenario: a move into the journal takes the diff lane
- **WHEN** a candidate renames a path outside `.agentmarshal/journal/` to a
  path under it
- **THEN** the candidate is not journal-only: the contract is read and the
  scope line names the source path

#### Scenario: a candidate without renames prints the transcript it printed before
- **WHEN** a candidate's range contains no rename
- **THEN** the gate's transcript is byte-for-byte what 0.3.0 printed for it
