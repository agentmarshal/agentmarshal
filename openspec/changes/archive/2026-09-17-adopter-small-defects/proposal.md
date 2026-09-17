## Why

Three findings from the same adopter batch, each small and each costing its
reporter real work.

[Proposal 020](../../../../docs/proposals/020-leak-scan-names-no-file-and-self-matches.md):
the leak scan refused a journal transaction with a category name and nothing
else — no file, no line, no matched marker — and the reporter checked twenty
file-and-marker combinations by hand to find the cause. The cause was the scan
matching a marker list against its own declaration, which happens to any adopter
who both captures diffs as evidence and declares markers in a versioned config.
This project now captures diffs as evidence, so it has one of those two
conditions already.

[Proposal 021](../../../../docs/proposals/021-reviewer-stderr-discarded-on-success.md):
the reviewer command's diagnostics are discarded on a zero exit. A wrapper that
degrades gracefully cannot say so; one that fails loudly is heard. Two defects
in the reporter's own wrapper were masked by this.

[Proposal 023](../../../../docs/proposals/023-upstream-outbox-has-no-transaction.md):
the outbox this tool creates for adopter findings sits beside the journal, and
a wrapper that stages the project directory sweeps whatever is in it into an
unrelated commit. Nothing says the outbox is not evidence.

## What Changes

- A leak-scan hit names the file and the marker or signature that matched, in
  the standalone command and at the merge boundary.
- A marker is not matched against the configuration that declares it.
- The reviewer command's error output is kept on the success path and the
  operator is told where.
- The shipped outbox README says the outbox is not journal evidence and gives
  the pathspec that excludes it from journal staging.

## Impact

- `src/agentmarshal/cli.py` and the leak-scan implementation it calls.
- `src/agentmarshal/journal/review.py`.
- `src/agentmarshal/project.py`, which writes the outbox README.
- No gate line changes; the merge-boundary warning gains detail.
