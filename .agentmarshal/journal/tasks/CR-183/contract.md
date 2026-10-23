+++
schema = 2
id = "CR-183"
title = "agentmarshal record-check records what a pipeline check found on a commit, its full output kept locally and a masked excerpt on the record"
scope = [
  "src/agentmarshal/record_check.py",
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/capture.py",
  "tests/",
  "openspec/changes/record-check-command/",
  "openspec/changes/archive/",
  "openspec/specs/review-evidence/",
]
acceptance = [
  "the change record-check-command has a proposal, a design.md and a delta spec on the capability review-evidence with ADDED requirements for the command; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal record-check --task <id> --commit <rev> --name <check> --result passed|failed|error|skipped` with optional `--failed-step`, `--run-url` and `--output-file` writes one `check` record through `create_check_record`; the commit is resolved to its full 40-hex id in the journal's repository and must exist there; the command is registered from its own module the way the `step` group is",
  "with `--output-file` the file's full content is kept in the clone's local state and announced in the process log as a `check-output` event carrying the task, the check name, the commit, the kept file's path and its sha256 — the mechanism review prose uses — and the record's `excerpt` is the content's last 4 KiB at most, cut on a UTF-8 character boundary with undecodable bytes replaced, so the failing end survives; without the flag the record carries no excerpt and no event is written",
  "the excerpt passes the leak scan, with the project's private markers, before it is written: a hit does not refuse the record — each matched span is replaced by `[masked: <category>]` and the command names the categories, never the matched text; if the masked excerpt still trips the scan (a private marker that occurs in the mask label itself), the record carries no excerpt and the command says the excerpt was withheld, still naming the categories; the masking lives beside the scan in capture.py and `agentmarshal leak-scan`'s behaviour and output are unchanged",
  "a refusal — unknown task, commit not found, a result outside the vocabulary, a value the record rules refuse, an unreadable output file — writes no record and no event; a task that is completed or abandoned accepts the record, as a measurement admitted after a terminal record; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/review-evidence/"]
decisions = ["ADR-0017", "ADR-0022"]
+++

# agentmarshal record-check

## Context

ADR-0017 decision 1: what a pipeline check found on a commit is evidence —
its name, its result, the step that failed, a short excerpt passed through
the leak scan, and a link to the run — while the full output goes to the
process log. ADR-0022 section 3 gives the `check` record (`excerpt` up to
4 KiB, `recorded_by` required), admitted after any terminal record as a
measurement, and section 7 the `check-output` event. CR-167 landed the
record; nothing writes it yet.

A hit in an excerpt is masked and marked rather than refused: the check's
result is the fact being recorded, and refusing it over a token printed in
a log would lose the fact with no path to record it. The unmasked full
output stays on the machine that ran the check, in local state that is
never versioned.

## Objective

A pipeline's verdict on a commit can be put on the record by one command,
with enough of its output to see why it failed and none of its secrets.

## Acceptance Criteria

As in the header.

## Non-Goals

- `brief` naming the last failed check, and `report` counting refusals
  (later tasks).
- A CI integration that calls the command; templates for providers.
- Masking anything beyond the excerpt; scanning the full output kept in
  local state.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md), including against processes of the same OS user.
