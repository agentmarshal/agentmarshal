# gate-lanes Specification (delta)

## Purpose

The operational lane of ADR-0013 decision 17: a candidate whose diff
only switches shared extensions — `.agentmarshal/switches.toml` beside
its own task's journal records — is admitted without a review, and the
extensions' `pre-gate` stages do not run on it.

## ADDED Requirements

### Requirement: an operational change takes its own gate lane

In the embedded placement, a candidate whose changes from the merge
base are `.agentmarshal/switches.toml` and otherwise nothing outside
`.agentmarshal/journal/tasks/<task>/` SHALL take the operational lane
when the task's contract — read from the merge-base tree when the task
exists there, and read from the candidate's tree when the candidate
opens the task — declares `scope` exactly
`[".agentmarshal/switches.toml"]`. On that lane the transcript SHALL
print one PASS line for the transaction; the review, verdict,
independence and agreement checks SHALL be reported NOT EXAMINED — the
operational change requires none of them — and every check that does
not depend on a review SHALL run as on the diff lane. A candidate whose
contract declares any other scope, or whose diff touches any other
path — a manifest, any configuration, code — SHALL take the lane it
takes today and need a review. In a sidecar the operational lane SHALL
NOT be offered.

#### Scenario: the operational lane admits a switches-only candidate

- **WHEN** the embedded candidate changes `.agentmarshal/switches.toml`
  and adds records under its own task's journal directory, and the
  task's contract at the base declares scope exactly
  `[".agentmarshal/switches.toml"]`
- **THEN** the transcript prints one PASS line for the operational
  transaction, NOT EXAMINED lines for the latest-review, reviewer
  independence and agreement checks, and every other check runs as it
  does today — the gate passes with no review record

#### Scenario: the contract is read from the base when the task exists there

- **WHEN** the task exists at the base and the candidate amends the
  contract inside its own journal subtree
- **THEN** the base's contract decides the lane: the candidate still
  takes the operational lane

#### Scenario: a task opened within the candidate reads the candidate's contract

- **WHEN** the base holds no `contract.md` for the task and the
  candidate adds the task's `contract.md` and `opened` record beside
  `.agentmarshal/switches.toml`, the added contract declaring scope
  exactly `[".agentmarshal/switches.toml"]`
- **THEN** the candidate takes the operational lane

#### Scenario: a contract declaring another scope does not take the lane

- **WHEN** the diff touches only `.agentmarshal/switches.toml` and the
  task's records but the contract's scope is not exactly
  `[".agentmarshal/switches.toml"]`
- **THEN** the candidate does not take the operational lane and the
  regular lane judges it — outside the declared scope and needing a
  review

#### Scenario: an extra path in the diff takes the lane it takes today

- **WHEN** the candidate changes `.agentmarshal/switches.toml` and a
  manifest, a configuration or a code path as well
- **THEN** the candidate takes the regular lane and needs a review

#### Scenario: in a sidecar the operational lane is not offered

- **WHEN** a sidecar's host candidate would satisfy the lane's shape
- **THEN** the transcript is the sidecar's regular-lane transcript and
  carries no operational-lane line

### Requirement: the operational lane verifies the switches file against the task and the base

On the operational lane the candidate's `.agentmarshal/switches.toml`
at the resolved commit SHALL be parsed by the shared switches parser
against the shared extension names the merge base declares. A file the
parse refuses — malformed TOML, a `format` other than `1`, an entry
outside its shape, an entry naming no shared extension the base
declares — SHALL refuse the candidate naming the file and, where the
parse reached one, the entry; a link or a non-blob at the file's path
refuses as not a file. Every entry the candidate adds or changes
relative to the base SHALL name the transaction's task in `task`; one
naming another task SHALL refuse the candidate naming the file and the
entry. An entry the base held and the candidate drops SHALL be allowed
— a removal is judged by the candidate having no entry, and switching
an extension back on is as operational as switching it off. An entry
the file carries unchanged from the base is not the candidate's claim:
its `task` is not consulted. Every value from the file SHALL be escaped
on display.

#### Scenario: a malformed switches file at the candidate refuses naming the file

- **WHEN** the candidate's `.agentmarshal/switches.toml` is not
  parseable — malformed TOML or a shape the parser refuses
- **THEN** the gate refuses, the refusal naming the file and, where one
  exists, the entry

#### Scenario: an undeclared extension entry is refused naming file and entry

- **WHEN** the candidate's file holds an entry whose name is not a
  shared extension the base enumerates
- **THEN** the gate refuses naming the file and the entry

#### Scenario: an entry naming another task is refused naming file and entry

- **WHEN** the candidate adds or changes an entry whose `task` is not
  this transaction's task
- **THEN** the gate refuses naming the file and the entry

#### Scenario: a removed entry is allowed

- **WHEN** the base's file holds an entry the candidate's file drops —
  or the candidate deletes the file
- **THEN** the candidate is not refused over the removal

#### Scenario: an unchanged entry naming another task is not refused

- **WHEN** the candidate's file keeps an entry the base held naming a
  different task, beside an entry this task adds or changes
- **THEN** the unchanged entry is not refused: the file carries it
  unchanged from a change that was already admitted

#### Scenario: a value that could forge a line is escaped on display

- **WHEN** a refused entry's name or value carries a forgeable
  character
- **THEN** the refusal prints it escaped

### Requirement: pre-gate stages do not run on an operational change

`stage run --phase pre-gate` on a candidate the gate's own predicate
qualifies for the operational lane SHALL print one line saying
pre-gate stages do not run on an operational change and SHALL run no
stage — no extension event, no pause — returning success. The decision
SHALL come from the same function the gate uses, imported rather than
copied. Every other phase and every other candidate SHALL behave as
today.

#### Scenario: pre-gate stages do not run on an operational change

- **WHEN** `stage run --phase pre-gate` is asked on a candidate taking
  the operational lane — one whose switched-off extension's
  `pre-gate-stop` stage would otherwise pause
- **THEN** the command prints one line saying pre-gate stages do not
  run on an operational change, runs no stage and exits 0

#### Scenario: other phases and other candidates behave as today

- **WHEN** `stage run` is asked for `post-gate` on an operational
  candidate, or for `pre-gate` on a candidate that is not operational
- **THEN** it behaves exactly as it does today — the post-gate stage
  runs, and the other candidate's pre-gate stages run
