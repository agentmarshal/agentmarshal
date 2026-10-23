## ADDED Requirements

### Requirement: A transaction adding another task's `opened` or `amendment` records warns without refusing

When the candidate adds a record path under
`.agentmarshal/journal/tasks/<task>/records/` whose `<task>` is not the
task the transaction names and whose record kind is `opened` or
`amendment`, the gate SHALL print one WARN line for all such records —
naming each affected task and the kinds it added, tasks and kinds in
sorted order — and SHALL continue to treat the records as valid
evidence: no violation is counted, the candidate is not refused over
them, and the records' own validity checks still run unchanged. Record
kinds other than `opened` and `amendment` — review, session, check and
the rest — SHALL produce no warning, as shall any record the judged
task's own directory adds. A candidate adding no such record SHALL
produce the transcript a run produces today, byte for byte. Every value
the line prints SHALL be escaped for display like every other value the
transcript prints.

#### Scenario: a candidate adding another task's opened record warns
- **WHEN** the candidate adds
  `.agentmarshal/journal/tasks/CR-002/records/<id>-opened.json` and the
  transaction names `CR-001`
- **THEN** the gate still passes the candidate and prints one WARN line
  naming `CR-002` and `opened`

#### Scenario: the one WARN line names each such task and the record kinds
- **WHEN** the candidate adds an `amendment` and an `opened` record of
  `CR-002` and an `opened` record of `CR-003`
- **THEN** one WARN line names `CR-002 (amendment, opened)` and `CR-003
  (opened)` and no other WARN line about the records prints

#### Scenario: records of other kinds do not warn
- **WHEN** the candidate adds a `session` record of `CR-002` and the
  transaction names `CR-001`
- **THEN** no WARN line about another task's records prints

#### Scenario: a candidate adding no such record produces today's transcript
- **WHEN** the candidate adds records only of the task it names — or
  none
- **THEN** the transcript is byte for byte what a run produces today
