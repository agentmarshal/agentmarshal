## MODIFIED Requirements

### Requirement: Nothing is required of a journal that keeps no prose
A review record without `artifacts` SHALL be read, gated and displayed as
before this capability existed; keeping prose is a capability, not an
obligation.

#### Scenario: an old journal reads as before
- **WHEN** a review record carries no `artifacts`
- **THEN** every command behaves as it did before this capability existed, and
  the gate's transcript for such a candidate is byte-for-byte the transcript
  the committed fixtures pin for a default run
