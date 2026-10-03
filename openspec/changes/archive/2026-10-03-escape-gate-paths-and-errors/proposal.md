## Why

CR-155 and CR-161 escape on display every value taken from a record or a
contract, the gate's transcript lines included. A candidate's file names
are neither, and the gate prints them as they are: a file named with a
newline could print a line the gate never said (`gate: passed` reads as
one), and a bidirectional override could make a name read in an order its
bytes do not have. The CR-161 review also found gate error and refusal
messages that carry values unescaped — a ref echoed in a failed git
command, an exception's text, git's own error output. Git quotes unusual
names unless told not to; the gate reads its path listings raw (`-z`), so
naming them safely is the tool's job.

## What Changes

- `GateError` escapes its message at construction — the one point a raise
  added later cannot forget — so every error and refusal text the gate
  produces prints each refused character as its escape, including messages
  raised by the context derivation and ones a lifecycle or review wrapper
  re-quotes.
- The gate's transcript already escapes each finished line (CR-161); this
  change pins that the same holds for every path the candidate names —
  paths outside contract scope, rename sources and targets, record paths,
  extension and manifest paths.
- record-text-safety gains a requirement for the gate escaping every value
  it did not write itself; scope-enforcement's change-set requirement is
  modified to say paths are named in escaped form.

## Capabilities

- modified: `record-text-safety`
- modified: `scope-enforcement`

## Impact

- `src/agentmarshal/journal/gate.py`: `GateError` escapes its message;
  transcript lines keep the escape point CR-161 gave them.
- `tests/test_gate.py`: new scenario tests — a candidate path carrying a
  newline and one carrying a right-to-left override are named escaped on
  the lines that name them; a rename's source with a newline is named
  escaped; a refusal embedding a forgeable ref prints it escaped; a
  byte-identical delegate.
- No fixture changes and no `cli.py` change: a candidate whose values
  carry no refused character renders byte-identically, and the CLI prints
  a `GateError`'s text as it stands — now escaped at birth.
