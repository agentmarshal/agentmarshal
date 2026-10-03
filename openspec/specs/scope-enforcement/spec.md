# scope-enforcement Specification

## Purpose
What the gate holds a candidate's paths to: the set of paths the candidate
touches, read from one listing in which a rename is its source deleted and
its destination added, compared against the contract's scope and the
footprints of the extensions it names. The check that keeps a candidate
inside what its contract declared, on whichever lane it takes.

## Requirements

### Requirement: A candidate's change set names every path it touches
The gate SHALL derive the set of paths a candidate changes from one listing in
which a rename contributes its source as a deletion and its destination as an
addition, and a copy contributes its destination as an addition. Every check
that reads the candidate's paths — the scope check, the choice between the
journal-only and diff lanes, and the refusal of an empty range — SHALL read
that set. A listing a check matches those paths against — the base tree
the record-collision check reads, the committed history the append-only
check reads — SHALL be read in the same raw form: a name git would
C-quote is matched by the path itself, never by the quoted form. Where
the gate names one of those paths — the scope line, the record-collision
and append-only lines, an extension's removal — it SHALL name it in
escaped form: a character that could add a line to the transcript or
reorder it prints as `\n`, `\r`, `\t` or its `\uXXXX` (`\UXXXXXXXX`)
escape, and a path carrying none prints as it is.

#### Scenario: a rename out of scope is refused
- **WHEN** a candidate renames a path the contract's scope does not cover to a
  path it does cover
- **THEN** the gate refuses the candidate and the scope line names the source
  path among the paths outside contract scope

#### Scenario: a rename within scope passes
- **WHEN** a candidate renames a path within the contract's scope to another
  path within it
- **THEN** the scope line passes with the wording it had before

#### Scenario: a move into the journal takes the diff lane
- **WHEN** a candidate renames a path outside `.agentmarshal/journal/` to a
  path under it
- **THEN** the candidate is not journal-only: the contract is read and the
  scope line names the source path

#### Scenario: a candidate without renames prints the transcript it printed before
- **WHEN** a candidate's range contains no rename
- **THEN** the gate's transcript is byte-for-byte the transcript the
  committed fixtures pin for a default run

#### Scenario: a path carrying a refused character is named in escaped form
- **WHEN** a path the change set names — touched, or a rename's source or
  target — carries a character that could add a line or reorder one
- **THEN** the line that names it prints each such character as its escape:
  the name adds no line and reorders none

#### Scenario: an unusual file name is matched by its real path, not git's quoted form
- **WHEN** a listing a check matches the candidate's paths against — the
  base tree, the committed history — holds a name git would C-quote
- **THEN** the check reads the listing NUL-separated and matches by the
  name itself, never by the quoted form
