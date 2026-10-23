+++
schema = 2
id = "CR-207"
title = "A journal-transaction script under templates stages only its own task's journal directory, and the documented recipes stop sweeping other tasks' records"
scope = [
  "templates/journal-transaction.sh",
  "src/agentmarshal/project.py",
  "docs/quickstart.md",
  "docs/sidecar.md",
  "docs/proposals/019-journal-transactions-assume-direct-commits.md",
  "docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md",
  "tests/",
  "openspec/changes/journal-transaction-template/",
  "openspec/changes/archive/",
  "openspec/specs/outbox/",
]
acceptance = [
  "templates/journal-transaction.sh, run as `journal-transaction.sh <task-id> <slug> <message-file>` from a clean checkout of the default branch, creates a branch whose name carries the task id (proposal 017's requirement), stages `.agentmarshal/journal/tasks/<task-id>/` and nothing else — by a literal pathspec — commits with the message file, pushes the branch to the remote named by `AM_REMOTE` (default `origin`), and prints that a pull request is the next step; opening the request is left to the adopter, the provider-specific line marked as the place to adapt; the script is POSIX sh or bash with `set -eu`, and its header says what it does and does not do",
  "before committing, the script lists every other changed or untracked path under `.agentmarshal/journal/` and does not stage it; it refuses, staging nothing, when the task's directory has no change, when the task id is not of the `CR-<n>` form, or when the checkout is not on the default branch — each refusal naming the reason; a test runs the script in a temporary repository and shows another task's record left unstaged and listed",
  "the outbox README `init` writes (src/agentmarshal/project.py) tells the reader to stage one task's directory — `git add .agentmarshal/journal/tasks/<task-id>` — instead of the whole journal, and keeps the outbox exclusion; if a requirement in openspec/specs/outbox/ pins that text, it is changed through an OpenSpec change (MODIFIED), archived with the archive command",
  "docs/quickstart.md's journal-transaction examples and docs/sidecar.md's `git add -A` examples stage the one task's directory, and the quickstart names the template script as the worked example; proposals 019 and 035 each carry a dated line in their Where section saying where the pattern and the script are now",
  "no command's behaviour changes; the gate's fixtures and every documented transcript a test pins are unchanged, or updated where this task changes the documented text itself; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = [
  "templates/journal-transaction.sh",
  "docs/quickstart.md",
  "docs/proposals/019-journal-transactions-assume-direct-commits.md",
  "docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md",
]
decisions = ["ADR-0012"]
+++

# A journal transaction that takes only its own task

## Context

Proposal 019's disposition: the journal-transaction pattern ships as a
documented pattern with a script under the templates directory, not a CLI
command — a command would have to know providers, protection schemes and
merge policies, the harness layer the project stays out of. Proposal 035's
disposition makes the constraint part of that work: the helper takes only
its own task's journal directory and lists anything else uncommitted
instead of taking it — more than a quarter of one adopter's journal
transactions carried other tasks' records until their wrapper stopped. The
sweeping recipe is also the one the project's own `init` writes into the
outbox README and its quickstart shows. ADR-0012 lists the template among
what the project supplies.

The gate warning about another task's `opened`/`amendment` records and the
`status` listing of unpublished records are the other half of 035 — a later
task.

## Objective

An adopter copying the project's recipe or script stages one task's
evidence per transaction.

## Acceptance Criteria

As in the header.

## Non-Goals

- A CLI command for transactions (declined by proposal 019's disposition).
- Opening the pull request through any provider's API.
- The gate warning and the `status` listing (a later task).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
