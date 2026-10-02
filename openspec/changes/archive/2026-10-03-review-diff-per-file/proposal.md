## Why

Proposal 037: `agentmarshal review` fails with a traceback on a diff that is
not UTF-8 — its git helper decodes the merge-base diff strictly before the
reviewer is launched, so one file's undecodable bytes take the whole review
down. The leak-scan half of the same root cause landed in
`per-file-leak-scan`, which built a helper that reads git's diff as bytes and
decodes it per file, naming what does not decode. This change brings `review`
onto it. The published disposition: a diff that is not wholly text must still
reach the reviewer, or be refused — per file, naming it.

Three advisories carried from that change's review land here because they
touch the same helper and its documentation: the C-quoted branch of the
diff-header name helper keeps the `b/` prefix its docstring says it drops;
`docs/sidecar.md`'s list of lines the gate's scan can append lacks the
undecodable-files line; and two test docstrings state `\x0c` as a literal
control character rather than an escape.

## What Changes

- `review` captures the merge-base diff as bytes and decodes it through
  `decode_diff_per_file`, the helper the leak scan already uses: a file whose
  section does not decode costs its own readability, not the launch.
- The reviewer is told what it could not be shown: the prompt names each file
  that did not decode and says how its unreadable bytes are marked, and the
  command's own output names the same files, masked with the project's
  configured markers the way the leak scan's warning masks them.
- Every other git output the launch reads — merge-base, ls-tree, rev-parse,
  error text — decodes with escapes rather than strictly, so a path whose
  bytes are not UTF-8 is named in printable form and no traceback escapes.
- The C-quoted branch of the diff-header name helper drops the `b/` prefix;
  the sidecar documentation lists the undecodable-files warning; the two
  docstrings carry `\x0c` as text.

## Capabilities

- modified: `reviewer-adapter`

## Impact

- `src/agentmarshal/journal/review.py`: byte-capturing git helper, per-file
  diff decode, the reviewer-facing caveat, the operator-facing note.
- `src/agentmarshal/journal/capture.py`: the header-name fix.
- `tests/`: the reproduction and the scenario tests.
- `docs/sidecar.md`: the missing transcript line.
