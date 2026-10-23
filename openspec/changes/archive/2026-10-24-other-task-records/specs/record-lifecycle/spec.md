## ADDED Requirements

### Requirement: `status --base` lists the task's records the ref does not hold

`agentmarshal status <task> --base <ref>` SHALL print, after the detail
view the command prints today and before any process-log lines, the
task's records present in the journal's working tree whose paths the
tree of `<ref>` does not hold: a header naming the ref as given, then
one `- <id> <type>` line per record in the task's stored order — or one
line naming the ref and saying there are none. The comparison SHALL be
by record path — a path the ref's tree holds is published whatever its
content there — and SHALL run in the repository the journal lives in:
the project repository in the embedded placement, the sidecar
repository in the sidecar placement, never the host repository's refs.
`<ref>` SHALL resolve to a commit or the command refuses, nonzero,
naming the ref as given — printing no part of the view first. `--base`
without a named task SHALL refuse, because the listing is per task.
Without `--base` the command SHALL print exactly what it prints today.
Every value the listing prints — the ref, the record id, the record
type — SHALL be escaped for display like every other value the view
prints.

#### Scenario: records the ref does not hold are listed
- **WHEN** the working tree holds records whose paths the tree of the
  named ref does not — a session and an amendment written since the
  commit the ref names
- **THEN** after the detail view a header names the ref and one line
  each prints the record's id and type

#### Scenario: no records the ref lacks prints one line
- **WHEN** every record path the working tree holds is held by the
  ref's tree
- **THEN** one line after the detail view names the ref and says there
  are none

#### Scenario: without --base the view is unchanged
- **WHEN** `status <task>` runs with no `--base`
- **THEN** the output is byte for byte what it prints today

#### Scenario: an unknown ref refuses naming it
- **WHEN** the named ref resolves to no commit in the journal's
  repository
- **THEN** the command returns nonzero, names the ref as given on
  stderr, and prints no part of the view

#### Scenario: a sidecar compares against the journal repository's ref
- **WHEN** the journal lives in a sidecar repository and the named ref
  is a commit of that repository — not of the host's
- **THEN** the listing answers against the sidecar's tree, and the
  host's refs are never consulted

#### Scenario: a value the listing prints is escaped on display
- **WHEN** the ref as given carries a character display refuses
- **THEN** the refusal — as the listing's lines would — prints the
  value's escaped form

#### Scenario: --base without a task is refused
- **WHEN** `status --base <ref>` runs with no task named
- **THEN** the command refuses, nonzero, saying the flag applies only to
  a named task
