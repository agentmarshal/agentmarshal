## Why

Reviews of CR-190 and CR-193 left advisory findings, deferred to this
task: the mark an acknowledged hit carries is built twice — `cli.py`
for `leak-scan`, `capture.py` for the gate — though CR-193's design
says it is shared; the leak-scan specification promises only that the
mark is escaped, while the code also masks it and CR-190's design says
the matched text cannot reach it; `acknowledge.py`'s docstring still
says acknowledgements are not honoured; and the sidecar read path the
reads requirement names, like `leak-scan --help`'s listing of
`--task`, is untested. None of the findings is a behaviour defect;
each is a document or a coverage that is untrue.

## What Changes

- The mark is built once: `cli.py` drops its private copies of
  `_acknowledgement_identification` and `_acknowledgement_mark` and
  calls `capture.py`'s `_acknowledgement_mark`, which the gate already
  calls — the one-line switch CR-193's design deferred.
- The specification's two mark requirements say what the code does:
  the mark — who acknowledged it and the reason — is masked by the
  leak scan and escaped on display, and the gate's requirement states
  the mark is the one mark-builder the two surfaces share.
- The reads requirement gains the sidecar scenario ADR-0014 describes:
  the records are read from the journal repository's working tree
  while the candidate is resolved and scanned in the host.
- `acknowledge.py`'s docstring no longer says acknowledgements are not
  honoured, and each archived design gains a dated correction line —
  the rest left as written.

## Capabilities

- modified: `leak-scan`

## Impact

No behaviour changes in any command: `leak-scan`'s output and exit and
the gate's advisory line are byte for byte what they are, which the
existing suites pin unchanged. What changes is who owns the mark's
code and what the documents say of it.
