+++
schema = 2
id = "CR-228"
title = "outbox check and send skip files already sent, so an outbox that predates the outbox group can send new findings"
scope = [
  "src/agentmarshal/outbox.py",
  "tests/",
  "openspec/changes/outbox-skips-sent/",
  "openspec/changes/archive/",
  "openspec/specs/outbox/",
]
acceptance = [
  "the change outbox-skips-sent has a proposal, a design.md and a delta spec on the capability outbox (ADDED requirements, MODIFIED where an existing requirement says every regular file but README.md is checked — full text, heading byte for byte, every scenario); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`outbox check` and `outbox send` treat as already sent, and do not check, a file whose sha256 is listed in the outbox's sent manifest (a file in the outbox, one `<sha256>  <name>` line each) or — when `--index <file>` is given, the same index `outbox status` takes — claimed by a `Source:` line of that index; each command prints one line `skipped as sent: <n>` when it skipped any, so skipping is never silent",
  "`outbox send` adds the hashes of the drafts it sends to the sent manifest in the same batch commit, so a later `check` skips them without an index; a sent file whose bytes changed since is not skipped — it is checked like a draft, and the check names it as changed after sending",
  "an entry of the outbox that is not a regular file (a subdirectory) is reported on one line and skipped, not counted as a failed draft; README.md stays skipped as today; an outbox with no sent manifest and no `--index` behaves exactly as today, which the existing outbox tests demonstrate unchanged",
  "every value shown is escaped as today; the leak scan still covers every file `send` stages; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/outbox/"]
decisions = ["ADR-0020"]
+++

# outbox skips files already sent

## Context

An adopter's finding (digest 045, staged 2026-10-24): an outbox created by
hand before the `outbox` group existed holds ten findings, nine already
sent; their sha256 links each to its public digest, so they cannot be
rewritten into the draft form. `outbox check` judges every regular file
but README.md as a draft and refuses the batch; `outbox send` runs the
check first, so it cannot be used at all. `outbox status --index` already
matches outbox files against an index's `Source:` lines by sha256.

## Objective

An outbox that predates the group can start sending new findings without
rewriting what it already sent.

## Acceptance Criteria

As in the header.

## Non-Goals

- Changing the draft form.
- Rewriting or moving files already sent.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
