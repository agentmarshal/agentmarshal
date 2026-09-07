## MODIFIED Requirements

### Requirement: A review may carry the reviewer's prose as a pinned artifact
A review record MAY carry `artifacts`: a list of `{ref, hash}` where `ref` is
a path relative to the project root under
`.agentmarshal/journal/tasks/<task>/artifacts/` and `hash` is the sha256 of
that file's bytes. When a review path keeps prose, it SHALL keep the
reviewer's output as received, unedited, and SHALL write the file before the
record that pins it. Once the prose is pinned, the review path SHALL keep no
other copy of it outside the journal.

#### Scenario: the model review path keeps its output
- **WHEN** `agentmarshal review` receives reviewer output that yields a valid verdict
- **THEN** the launcher writes that output to
  `.agentmarshal/journal/tasks/<task>/artifacts/<review-record-id>-review.md`
  and the review record it writes carries one artifact pinning that file

#### Scenario: an accepted verdict keeps no copy outside the journal
- **WHEN** `agentmarshal review` has pinned the reviewer's output
- **THEN** it writes no copy of that output anywhere else, and tells the
  operator the artifact's path and nothing about a temporary file

#### Scenario: the human review path attaches prose
- **WHEN** `agentmarshal submit-review` is given `--prose <file>`
- **THEN** the file's bytes are copied to the same location and pinned on the
  record; without `--prose` the record carries no `artifacts`, as today

#### Scenario: a rejected verdict still keeps the prose
- **WHEN** reviewer output fails verdict validation
- **THEN** the output is kept where the operator can read it, as today, and
  no review record is written

### Requirement: The prose is visible where the record is
`status` SHALL show, on the line of a review record that carries `artifacts`,
how many it carries; `report`, which has no per-record line, SHALL show on
the task's line the total over the task's review records.

#### Scenario: status names the prose
- **WHEN** `agentmarshal status <task>` lists a review record that carries `artifacts`
- **THEN** the review line says how many artifacts it carries

#### Scenario: report totals the prose
- **WHEN** `agentmarshal report --task <task>` reports a task whose review
  records carry artifacts
- **THEN** the task's line shows the sum over those records

## ADDED Requirements

### Requirement: A refused record leaves no artifact behind
A review path SHALL refuse a record for every reason the record writer can
check before writing — its shape, its finding binding, its task, the
recorder's identity — before the record's artifact is written, and SHALL do
so through the same checks the writer applies, stated once.

#### Scenario: a binding to an unknown finding writes nothing
- **WHEN** `submit-review --reviewed-finding <id> --prose <file>` names a
  finding the task does not have
- **THEN** the command refuses, and no file appears under the task's
  artifacts directory

#### Scenario: a refusal the writer cannot foresee is named as a limit
- **WHEN** the record write itself fails after the artifact is written (a
  filesystem error, an id collision)
- **THEN** the command reports the failure and names the artifact it left,
  so the operator can decide what to do with it

### Requirement: Artifact paths follow the record collision rule
The gate SHALL refuse a candidate that adds a path under
`.agentmarshal/journal/tasks/<task>/artifacts/` which already exists in the
base tree, as it refuses such a record path.

#### Scenario: two candidates add the same artifact path
- **WHEN** a candidate adds an artifact path that the base tree already holds
- **THEN** the gate reports the collision and refuses the candidate
