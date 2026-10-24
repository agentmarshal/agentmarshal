# extension-stages Specification (delta)

## ADDED Requirements

### Requirement: an accepted pause stands down a pre-gate-stop stage's pause for the accepted extension and commit

At `--phase pre-gate`, when a `pre-gate-stop` stage's decision is
`failed`, `did-not-finish` or `not-run`, the command SHALL look in the
task's acceptance records — read through `read_records` from the
journal the placement names, never a second parser — for an
`acceptance` record carrying `accepted_pause` naming the stage's
extension and `accepted_commit` equal to the commit the run resolved
(ADR-0013 decision 5, ADR-0022 section 2); where several match, the
latest in journal order applies. An acceptance bound to another
commit, naming another extension, or of another form — `findings` or
`operational` — SHALL NOT count. With a match the stage's result line
SHALL keep its outcome and add `, pause accepted by <party> (<reason>)`
— `<party>` the record's `accepted_by`, `<reason>` the record's
`reason`, each escaped for display — and the stage SHALL NOT pause the
process. The stage's `extension-event` SHALL carry the decision it
carries today, and its `reason` SHALL name the acceptance record: the
reason it carries today followed by `; pause accepted by acceptance
record <id>`, the record's id as `read_records` yields it — or that
clause alone where the stage's reason is empty. A `checked` stage and a
`switched-off` stage SHALL NOT consult an acceptance — a checked
stage's line never mentions one — and neither SHALL a `pre-gate-warn`
stage nor a `post-gate` stage, whose outcomes are unchanged. The
journal SHALL be read lazily, at the first `pre-gate-stop` stage whose
decision calls for it, so a run that pauses nothing never opens it; a
journal that cannot be read SHALL be named on one stderr line and
every pause SHALL stand — the fallback never lifts a pause.

#### Scenario: an accepted pause lets the process continue naming who accepted
- **WHEN** a `pre-gate-stop` stage's decision is `failed` and the task
  holds an acceptance carrying `accepted_pause` naming that extension
  and `accepted_commit` equal to the commit the run resolved
- **THEN** the result line reads `<name>: failed (exit <n>), pause
  accepted by <party> (<reason>)` naming the record's `accepted_by`
  and `reason`, no pause line is printed and the command exits 0

#### Scenario: an accepted pause stands down a did-not-finish or not-run stage the same way
- **WHEN** a `pre-gate-stop` stage's decision is `did-not-finish` or
  `not-run` and a matching acceptance stands
- **THEN** the result line keeps its outcome and adds the
  `pause accepted by <party> (<reason>)` suffix, and the command exits
  0 when no other stage pauses

#### Scenario: the latest matching acceptance in journal order is the one named
- **WHEN** two acceptances carry `accepted_pause` for the stage's
  extension and `accepted_commit` equal to the resolved commit
- **THEN** the result line and the extension-event name the later
  record

#### Scenario: an acceptance bound to another commit does not count
- **WHEN** the task's `accepted_pause` acceptances for the extension
  bind commits other than the one the run resolved
- **THEN** the stage pauses as before and the command exits 3

#### Scenario: an acceptance naming another extension does not count
- **WHEN** the task's `accepted_pause` acceptance at the resolved
  commit names a different extension
- **THEN** the stage pauses as before and the command exits 3

#### Scenario: an acceptance of another form does not count
- **WHEN** the task's acceptances at the resolved commit carry
  `findings` or `operational` and none carries `accepted_pause` for the
  extension
- **THEN** the stage pauses as before and the command exits 3

#### Scenario: an accepted pause lifts no other stage's pause
- **WHEN** one `pre-gate-stop` extension's pause is accepted and a
  second `pre-gate-stop` stage pauses with no matching acceptance
- **THEN** the accepted stage's result line carries the
  `pause accepted by` suffix, the second stage's pause stands and the
  command exits 3

#### Scenario: a checked stage's line never mentions an acceptance
- **WHEN** a `pre-gate-stop` stage's decision is `checked` and a
  matching acceptance stands
- **THEN** the result line is `<name>: checked` with no suffix

#### Scenario: a pre-gate-warn stage is unchanged by an acceptance
- **WHEN** a `pre-gate-warn` stage's decision is `failed` and an
  `accepted_pause` acceptance names the extension at the resolved
  commit
- **THEN** the warning prints, no `pause accepted by` suffix appears
  and the command exits 0

#### Scenario: a post-gate stage is unchanged by an acceptance
- **WHEN** a `post-gate` stage's decision is `failed` and an
  `accepted_pause` acceptance names the extension at the resolved
  commit
- **THEN** its result line is unchanged and the command exits 0

#### Scenario: a switched-off stage is unchanged by an acceptance
- **WHEN** a `pre-gate-stop` extension is switched off at the base and
  an `accepted_pause` acceptance names it at the resolved commit
- **THEN** the result line is `<name>: switched off (<task>,
  <reason>)` with no `pause accepted by` suffix and no pause

#### Scenario: the extension-event of an accepted pause names the acceptance record
- **WHEN** an accepted `pre-gate-stop` stage's result is appended to
  the process log
- **THEN** the event carries the decision it carries today and a
  `reason` ending `pause accepted by acceptance record <id>` naming
  the record's id

#### Scenario: a record's values are escaped on display
- **WHEN** an acceptance's `accepted_by` or `reason` reaching the
  suffix carries a forgeable character
- **THEN** the displayed line carries the escape, not the character

#### Scenario: a journal that cannot be read names it and every pause stands
- **WHEN** a `pre-gate-stop` stage's decision calls for the acceptance
  read and the journal cannot be read
- **THEN** one stderr line names the journal, the stage's result line
  carries no `pause accepted by` suffix, the pause stands and the
  command exits 3

## MODIFIED Requirements

### Requirement: a pre-gate-stop stage that did not check pauses the process before the gate

The command SHALL print that the process is paused before the gate —
naming the stage — and SHALL exit 3 when any `pre-gate-stop` stage's
decision is not `checked`: failed, did not finish or did not run —
unless the stage's pause is accepted under the accepted-pause
requirement, in which case the pause stands down as that requirement
states. A `pre-gate-warn` stage whose decision is not `checked` SHALL
print a warning naming it and SHALL NOT change the exit; a `post-gate`
stage SHALL never pause. Otherwise the command SHALL exit 0.

#### Scenario: a failed pre-gate-stop stage pauses the process before the gate
- **WHEN** a `pre-gate-stop` stage's decision is `failed`
- **THEN** the command prints that the process is paused before the
  gate naming the stage and exits 3

#### Scenario: a pre-gate-stop stage that did not run pauses the process
- **WHEN** a `pre-gate-stop` stage's decision is `did-not-finish` or
  `not-run`
- **THEN** the command pauses and exits 3 the same way

#### Scenario: a failed pre-gate-warn stage warns and the exit is 0
- **WHEN** a `pre-gate-warn` stage's decision is `failed`
- **THEN** the command prints a warning naming the stage and exits 0

#### Scenario: a checked pre-gate-stop stage does not pause
- **WHEN** every `pre-gate-stop` stage's decision is `checked`
- **THEN** nothing is paused and the command exits 0

#### Scenario: a post-gate stage's outcome never pauses
- **WHEN** a `post-gate` stage fails or does not run
- **THEN** the command exits 0 and prints no pause
