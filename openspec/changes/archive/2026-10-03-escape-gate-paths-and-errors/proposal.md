## Why

CR-155 and CR-161 escape on display every value taken from a record or a
contract, the gate's transcript lines included. A candidate's file names
are neither, and the gate prints them as they are: a file named with a
newline could print a line the gate never said (`gate: passed` reads as
one), and a bidirectional override could make a name read in an order its
bytes do not have. The CR-161 review also found gate error and refusal
messages that carry values unescaped — a ref echoed in a failed git
command, an exception's text, git's own error output — and the same is
true of the placement refusal the gate's CLI prints. Git quotes unusual
names unless told not to; naming them safely is the tool's job, and two
listings the gate matches names against still read git's quoted form.

## What Changes

- `GateError` escapes its message at construction — the one point a raise
  added later cannot forget — so every error and refusal text the gate
  produces prints each refused character as its escape, including messages
  raised by the context derivation and ones a lifecycle or review wrapper
  re-quotes.
- `_placement` in `cli.py` escapes a `PlacementError`'s text where the CLI
  prints it: the message can carry a sidecar host from `project.json` or
  git's own error text, values the tool did not write.
- The base tree's `git ls-tree -r --name-only` and the journal history's
  `git log --name-only` join the gate's other listings in reading `-z`:
  read quoted, a name git C-quotes never equals the raw name the
  candidate's diff returns, so a record-path collision or a committed
  tamper could hide from a matcher.
- Every NUL-separated listing decodes with `surrogateescape`: a name
  whose bytes are not UTF-8 keeps its bytes for matching and never
  refuses the run, and where the gate names it the surrogate prints as
  its `\uXXXX` escape — a surrogate is a character the forgeable-text
  rule refuses.
- The gate's transcript already escapes each finished line (CR-161); this
  change pins that the same holds for every path the candidate names —
  paths outside contract scope, rename sources and targets, record paths,
  extension and manifest paths.
- record-text-safety gains a requirement for the gate escaping every value
  it did not write itself; scope-enforcement's change-set requirement is
  modified to say paths are matched raw and named in escaped form.

## Capabilities

- modified: `record-text-safety`
- modified: `scope-enforcement`

## Impact

- `src/agentmarshal/journal/gate.py`: `GateError` escapes its message;
  the base-tree and history listings read `-z`; every `-z` listing
  decodes `surrogateescape`; transcript lines keep the escape point
  CR-161 gave them.
- `src/agentmarshal/cli.py`: `_placement` escapes a `PlacementError`'s
  text at the print point.
- `tests/test_gate.py`: new scenario tests — a candidate path carrying a
  newline and one carrying a right-to-left override are named escaped on
  the lines that name them; a rename's source with a newline is named
  escaped; a refusal embedding a forgeable ref prints it escaped; a
  placement refusal carrying a forgeable host prints it escaped; a
  collision and a tamper a quoted name would have hidden are found;
  a name whose bytes are not UTF-8 is named escaped without refusing
  the run, in the candidate and in the base tree; a byte-identical
  delegate.
- No fixture changes: a candidate whose values carry no refused
  character renders byte-identically.
