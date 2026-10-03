## ADDED Requirements

### Requirement: The gate escapes every value it did not write itself
A candidate's file names are record text no rule reaches: they are legal
in git and the gate reads them raw. Where the gate renders a value it did
not write — a candidate path the change set names, a rename's source or
target, a record path, an extension or manifest path, or a value carried
into an error or refusal message, an exception's text, a ref and git's
own error output included — every refused character SHALL print as its
escape: `\n`, `\r` and `\t` by name, `\uXXXX` (`\UXXXXXXXX` past the
Basic Multilingual Plane) for the rest, the same characters and forms the
display-escape rule uses, so nothing a candidate controls can add a line
to what the gate prints or make it read in an order its bytes do not
have. A value carrying no refused character SHALL print byte-identically.

#### Scenario: a candidate path that would forge a line is named in escaped form
- **WHEN** a candidate's change set names a path carrying a newline or a
  bidirectional override and the gate names it — on the scope line or a
  record-collision line
- **THEN** each refused character prints as its escape on the line that
  names it, and no line the name would have forged appears

#### Scenario: a rename's source or target carrying a refused character is named in escaped form
- **WHEN** a rename's source or target carries a refused character and
  the gate names it among the paths outside contract scope
- **THEN** it prints escaped on the line that names it

#### Scenario: a refusal names a forgeable value in escaped form
- **WHEN** an error or refusal message embeds a value taken from the
  candidate, the journal or git output — a ref, a path, an exception's
  text — that carries a refused character
- **THEN** the message prints the value escaped and stays the one line it
  was

#### Scenario: a candidate whose values carry no refused character prints as before
- **WHEN** every path and value the gate renders carries no refused
  character
- **THEN** the transcript and its refusals are byte-identical to what
  they were
