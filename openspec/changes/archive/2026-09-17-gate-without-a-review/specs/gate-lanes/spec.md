## ADDED Requirements

### Requirement: The gate can be asked to judge what does not depend on a review
The gate SHALL accept a request to evaluate the checks that do not depend on a
review record. In that mode, when the candidate has no review record at all, the
review-bound checks SHALL be reported as not examined, with the reason, and
SHALL NOT refuse the candidate. Every other check SHALL be evaluated as it is
without the mode.

#### Scenario: a candidate with no review passes the checks that do not need one
- **WHEN** the gate is asked to judge without a review and the candidate has no
  review record for its commit
- **THEN** the transcript reports the review-bound checks as not examined,
  naming the absence as the reason, and the gate's verdict rests on the
  remaining checks

#### Scenario: the mode does not excuse a candidate that breaks another rule
- **WHEN** the gate is asked to judge without a review and the candidate changes
  a path outside its contract's scope
- **THEN** the gate refuses, exactly as it does without the mode

### Requirement: The mode never weakens a candidate that has been reviewed
When a review record exists for the candidate, the review-bound checks SHALL be
evaluated whether or not the mode was requested, and their outcome SHALL be what
it is without it.

#### Scenario: a non-approving review still refuses
- **WHEN** the gate is asked to judge without a review and the candidate's
  latest review is non-approving
- **THEN** the gate refuses, and its transcript reports the review check as it
  does without the mode

#### Scenario: an approving review is reported as approving
- **WHEN** the gate is asked to judge without a review and the candidate's
  latest review is approving
- **THEN** the review-bound checks report their usual result and nothing says
  they were skipped

### Requirement: A default run is unchanged
A gate run that does not request the mode SHALL produce the transcript it
produces today, byte for byte, in every placement and on every lane.

#### Scenario: the pinned transcript still matches
- **WHEN** the gate runs without the mode on a candidate the pinned transcript
  test covers
- **THEN** its output is what the released version produced
