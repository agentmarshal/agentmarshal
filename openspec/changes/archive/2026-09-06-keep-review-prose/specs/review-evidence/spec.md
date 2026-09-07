## ADDED Requirements

### Requirement: A review may carry the reviewer's prose as a pinned artifact
A review record MAY carry `artifacts`: a list of `{ref, hash}` where `ref` is
a path relative to the project root under
`.agentmarshal/journal/tasks/<task>/artifacts/` and `hash` is the sha256 of
that file's bytes. When a review path keeps prose, it SHALL keep the
reviewer's output as received, unedited, and SHALL write the file before the
record that pins it.

#### Scenario: the model review path keeps its output
- **WHEN** `agentmarshal review` receives reviewer output that yields a valid verdict
- **THEN** the launcher writes that output to
  `.agentmarshal/journal/tasks/<task>/artifacts/<review-record-id>-review.md`
  and the review record it writes carries one artifact pinning that file

#### Scenario: the human review path attaches prose
- **WHEN** `agentmarshal submit-review` is given `--prose <file>`
- **THEN** the file's bytes are copied to the same location and pinned on the
  record; without `--prose` the record carries no `artifacts`, as today

#### Scenario: a rejected verdict still keeps the prose
- **WHEN** reviewer output fails verdict validation
- **THEN** the output is kept where the operator can read it, as today, and
  no review record is written

### Requirement: Review artifacts are evidence and follow the record rule
A review artifact, once written, MUST NOT be modified or deleted.

#### Scenario: the gate refuses a modified artifact
- **WHEN** a candidate modifies or deletes a file under
  `.agentmarshal/journal/tasks/<task>/artifacts/`
- **THEN** the gate reports it in the append-only check and refuses the
  candidate, as it does for a record

#### Scenario: the artifact's hash is checked where its record is validated
- **WHEN** `agentmarshal validate` reads a review record carrying `artifacts`
- **THEN** it refuses a journal whose artifact file is missing or whose bytes
  do not match the pinned hash

### Requirement: The prose is visible where the record is
`status` and `report` SHALL show, on the line of a review record that carries
`artifacts`, how many it carries.

#### Scenario: status names the prose
- **WHEN** `agentmarshal status <task>` lists a review record that carries `artifacts`
- **THEN** the review line says how many artifacts it carries, and `report`
  shows the same

### Requirement: Nothing is required of a journal that keeps no prose
A review record without `artifacts` SHALL be read, gated and displayed as in
0.3.0; keeping prose is a capability, not an obligation.

#### Scenario: an old journal reads as before
- **WHEN** a review record carries no `artifacts`
- **THEN** every command behaves as it did in 0.3.0, and the gate's
  transcript for such a candidate is unchanged
