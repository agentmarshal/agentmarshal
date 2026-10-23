## Why

ADR-0017 decision 1 decided what a pipeline check found on a commit is
evidence — its name, its result, the step that failed, a short excerpt
passed through the leak scan, and a link to the run — while the full
output goes to the process log (ADR-0022 section 7's `check-output`
event). CR-167 landed the record: the journal admits a `check` record,
a measurement admitted after any terminal record. What does not exist
yet is the way an observer writes one: the record type has no command,
so a pipeline's verdict — a passing check as much as a refused
candidate — cannot reach the journal except by hand.

## What Changes

- `agentmarshal record-check --task <id> --commit <rev> --name <check>
  --result passed|failed|error|skipped` writes one `check` record
  through `create_check_record`; `--commit` is resolved to its full
  40-hex id in the journal's repository and must exist there, and
  `--failed-step` and `--run-url` are optional. The command is
  registered from its own module the way the `step` group is.
- `--output-file <path>` keeps the file's full bytes under the journal
  repository's local state and announces them in the process log as a
  `check-output` event — the mechanism review prose uses — while the
  record's `excerpt` becomes the content's last 4 KiB at most, cut on
  a UTF-8 character boundary with undecodable bytes replaced, so the
  failing end survives. Without the flag the record carries no excerpt
  and no event is written.
- The excerpt passes the leak scan — the project's configured private
  markers included — before it is written: a hit is masked, not
  refused, each matched span replaced by `[masked: <category>]` while
  the command names the categories and never the matched text. The
  masking function lives beside the scan in `capture.py`; `agentmarshal
  leak-scan`'s behaviour and output are unchanged.
- A refusal — an unknown task, a commit that does not resolve, a result
  outside the vocabulary, a value the record rules refuse, an
  unreadable output file — writes no record, no event and no kept
  file; a completed or abandoned task admits the record, the
  measurement the record type is.

## Capabilities

- modified: `review-evidence`

## Impact

One new command and one new module, one new function beside the scan;
no other command's behaviour or output changes, and the gate's
transcript and fixtures are untouched. What a `check` record
guarantees stays what its observer declares — the gate decides nothing
from it, and nothing is added beyond the guarantees the threat model
publishes.
