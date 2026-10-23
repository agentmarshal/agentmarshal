# gate-lanes Specification

## Purpose
Which of the gate's checks a caller is in a position to ask for, and how the
transcript reports the ones it was not. A caller that cannot yet have a review —
a provider's CI, running on a head no review can name — gets everything else,
and reads what was left unexamined rather than inferring it from silence.

## Requirements

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
produces today, byte for byte, in every placement and on every lane — the
transcript pinned by fixtures committed in the repository, one for each
case the pin covers. A run's stdout, stderr and exit status
SHALL each equal the fixture for its lane and placement, compared after one
substitution replaces the values that differ from run to run — commit
hashes, temporary paths, record ids, times — with named placeholders, so
the comparison is exact everywhere else. Any change to a fixture SHALL be
made, and named, by the task that changes the output: the fixture is
regenerated only when the test is explicitly asked to, and the fixture's
diff is part of that task's reviewed change.

#### Scenario: the pinned transcript still matches
- **WHEN** the gate runs without the mode on a candidate the pinned
  transcript fixtures cover — the implementation lane and the journal-only
  lane in the embedded placement; in the sidecar placement the
  implementation lane and the host candidate whose diff touches only the
  journal, whose fixture pins the refusal because the deterministic lane
  does not exist there (ADR-0008 decision 2)
- **THEN** its stdout, its stderr and its exit status equal the committed
  fixture once run-dependent values are replaced by named placeholders

#### Scenario: a transcript difference is shown, not hidden
- **WHEN** a gate run's transcript differs from the committed fixture for
  its lane and placement
- **THEN** the pinned test fails and shows the difference as a readable
  diff between fixture and run

#### Scenario: a fixture changes only when the output changes on purpose
- **WHEN** a task changes the gate's default output on purpose
- **THEN** that task regenerates the fixtures — which the test rewrites
  only when explicitly asked — and the change to each fixture is part of
  the task's reviewed change, naming the output change it makes

### Requirement: The transcript reports the task's changes_required count
On the implementation lane — in the embedded placement and in a sidecar —
a gate run that evaluates a candidate SHALL print one line carrying the
task's count of `changes_required` review verdicts over the whole task —
every review record of the task's candidates, whatever commit it names; a
review bound to a research finding (ADR-0009) is not counted — and the
project's `review.changes_required_threshold` (default 3), read through
the project settings. When the count has reached the threshold the line
SHALL be marked, the signal to stop and revisit the contract. The line
reports; it decides nothing: it SHALL NOT add a violation, change the
run's exit status, or refuse a merge. A threshold setting that cannot be
read SHALL be named on the line and SHALL NOT fail the run.

#### Scenario: the implementation lane prints the count
- **WHEN** the gate evaluates a candidate on the implementation lane
- **THEN** the transcript carries one line naming the task's count of
  `changes_required` verdicts over every review record of the task's
  candidates and the project's threshold

#### Scenario: the count is over the whole task
- **WHEN** the task's earlier commits drew `changes_required` verdicts
  and the candidate's own latest review approves
- **THEN** the line's count covers every review record of the task's
  candidates, not only the records naming the candidate's commit

#### Scenario: a review bound to a research finding is not counted
- **WHEN** the task carries a `changes_required` review bound to a
  research finding (`reviewed_finding`, ADR-0009) alongside reviews of
  its candidates
- **THEN** the line's count covers only the reviews of the task's
  candidates; the finding's review is not a candidate's return

#### Scenario: a count at the threshold is marked
- **WHEN** the task's count of `changes_required` verdicts has reached
  the project's threshold
- **THEN** the count line is marked as reaching it, and the run's verdict
  and exit status are what they would be without the line

#### Scenario: a malformed threshold is reported on the line
- **WHEN** `review.changes_required_threshold` cannot be read as a valid
  threshold
- **THEN** the count line names the unreadable threshold, the count still
  prints, and the run is otherwise what it was

#### Scenario: the journal-only lane prints no count line
- **WHEN** a gate run takes the journal-only lane
- **THEN** its transcript carries no `changes_required` count line

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

### Requirement: an operational change takes its own gate lane

In the embedded placement, a candidate whose changes from the merge
base are `.agentmarshal/switches.toml` and otherwise nothing outside
`.agentmarshal/journal/tasks/<task>/` SHALL take the operational lane
when the task's contract — read from the merge-base tree when the task
exists there, and read from the candidate's tree when the candidate
opens the task — declares `scope` exactly
`[".agentmarshal/switches.toml"]`. On that lane the transcript SHALL
print one PASS line for the transaction and one PASS line for the
scope — `PASS: scope (operational lane: the diff is
.agentmarshal/switches.toml and the task's own records)` — because the
scope is enforced by the lane's own predicate: the admitted diff is the
switches file plus the task's own records and the contract's scope is
exactly that file. The review, verdict,
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
  transaction and one for the scope the lane's predicate enforced,
  NOT EXAMINED lines for the latest-review, reviewer
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
refuses as not a file. The merge base's own file SHALL parse under the
same parser against the same names before the lane is taken at all —
an absent file parses as no entries — and a base file the read or the
parse refuses keeps the candidate off the operational lane: the
candidate takes the lane it takes today and needs a review, because a
removal or an unchanged entry cannot be judged against a base that
cannot be read. The candidate's file SHALL be compared to the base's
as raw TOML — the tables `tomllib` reads of the same blob text the
parser read, not the parsed `Switch` entries, which drop the keys an
entry carries beyond `state`, `task` and `reason`. Every top-level
key other than `switches` SHALL be identical between the base's file
and the candidate's — an absent file counting as `format = 1` and
nothing else — or the candidate SHALL be refused naming the file.
For each entry name, when the candidate's raw entry table differs
from the base's — every key compared, so a key the parser does not
read marks the entry changed all the same — the candidate's entry
SHALL name the transaction's task in `task`; one naming another task
SHALL refuse the candidate naming the file and the entry. An entry
the base holds and the candidate drops SHALL refuse
the candidate naming the file and the entry — and a candidate that
deletes the file while the base held entries drops every one, refused
the same way. Switching an extension back on is not a removal but a
changed entry: `state = "on"` naming the transaction's task, so every
change the file carries names the task that made it. An entry the file
carries unchanged from the base — the whole raw table — is not the
candidate's claim: its `task` is not consulted. Every value from the
file SHALL be escaped on display.

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

#### Scenario: a removed entry is refused naming the file and the entry

- **WHEN** the base's file holds an entry the candidate's file drops —
  or the candidate deletes the file, dropping every entry it held
- **THEN** the gate refuses naming the file and each dropped entry

#### Scenario: a base file that cannot be read keeps the candidate off the lane

- **WHEN** the merge base's `.agentmarshal/switches.toml` is one the
  read or the parse refuses — malformed TOML, a well-formed file
  holding an entry outside its shape, or not a file at all — and the
  candidate's diff otherwise has the operational lane's shape
- **THEN** the candidate does not take the operational lane and takes
  the lane it takes today, needing a review: a removal or an
  unchanged entry cannot be judged against a base that cannot be read

#### Scenario: switching an extension back on names this task

- **WHEN** the base's file holds an `off` entry for an extension and
  the candidate's file changes it to `state = "on"` with `task` naming
  this task
- **THEN** the candidate is not refused over the entry: switching back
  on is a changed entry like any other, naming the task that made it

#### Scenario: an unchanged entry naming another task is not refused

- **WHEN** the candidate's file keeps an entry the base held naming a
  different task, beside an entry this task adds or changes
- **THEN** the unchanged entry is not refused: the file carries it
  unchanged from a change that was already admitted

#### Scenario: a change outside the parsed fields is still a change

- **WHEN** the candidate's file differs from the base's only where the
  parsed `Switch` drops it — an extra key on an entry that still names
  another task, or a top-level key outside `switches`
- **THEN** the gate refuses the candidate naming the file — and the
  entry when an entry's table differs — because the lane compares the
  raw TOML, so a difference the parser does not keep is a difference
  all the same

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
