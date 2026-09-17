# trust-preconditions Specification

## Purpose
What this tool's guarantees rest on that it cannot establish itself, and what it
owes an operator about them: to name them once at `init`, and to report the ones
it can reach without a network or a credential — never claiming a check passed
where none was made.

## Requirements

### Requirement: `init` names the preconditions it cannot verify
`init` SHALL print, once, the configuration its guarantees depend on and that it
cannot itself establish, and SHALL say for each what is lost if it is skipped.
It SHALL NOT attempt to configure a provider or a harness.

#### Scenario: a fresh project is told what remains
- **WHEN** `agentmarshal init` completes in a new project
- **THEN** its output lists the preconditions, including that squash and rebase
  merges rewrite a reviewed SHA and that an agent's harness must declare its
  actor, each with what it costs to skip

### Requirement: `doctor` checks the preconditions it can reach
`doctor` SHALL report on the actor variable, on whether the configured reviewer
command's placeholders resolve, and on whether a CI definition invoking
`validate` exists. Each report SHALL say what the missing piece costs. A missing
precondition SHALL NOT make `doctor` exit non-zero unless it already would: this
is a report, not a gate.

#### Scenario: an unset actor variable is reported
- **WHEN** `doctor` runs where no actor variable is set
- **THEN** it reports that records will resolve to the invoking git identity,
  and does not report all checks as passing

#### Scenario: a reviewer command with an unresolvable placeholder is reported
- **WHEN** `doctor` runs with a reviewer command whose placeholders the launcher
  would reject
- **THEN** it reports that a review cannot launch, without printing the
  command's value

#### Scenario: a project with every precondition met reports so
- **WHEN** `doctor` runs where the actor variable, the reviewer command and a CI
  definition invoking `validate` are all present
- **THEN** it reports them as met and its exit status is what it was before this
  change
