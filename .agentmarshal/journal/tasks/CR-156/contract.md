+++
schema = 2
id = "CR-156"
title = "outbox send makes one batch commit of the outbox after the check; outbox status reports from an index file which drafts upstream claims"
scope = [
  "src/agentmarshal/outbox.py",
  "src/agentmarshal/cli.py",
  "tests/",
  "openspec/changes/outbox-send-and-status/",
  "openspec/changes/archive/",
  "openspec/specs/outbox/",
]
acceptance = [
  "the change outbox-send-and-status has a proposal, a design.md and a delta spec modifying the outbox capability (MODIFIED requirements keep their exact headers, ADDED for new ones); every scenario in the delta is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal outbox send` runs the check first and refuses on any failure; it refuses when anything outside the outbox is already staged; otherwise it stages only `.agentmarshal/upstream/` and makes exactly one commit of the batch with a message naming the files, and prints the commit; it transmits nothing and opens no network",
  "`agentmarshal outbox status --index <file>` hashes each file in the outbox (sha256 of the file as it is, lowercase hex) and compares the hashes with the `Source:` lines of the index file the operator names, printing for each outbox file whether an entry claims it and which, and listing index entries that match no file; a missing or unreadable index is refused with a message; no network",
  "a file name in the outbox that is not UTF-8 is named in an escaped printable form, never crashing `check`, `send` or `status` with a traceback (a carried advisory: it crashes `check` today), and every printed name keeps the masking `check` applies",
  "the commands register from src/agentmarshal/outbox.py (cli.py keeps only the hook), and the full CI sequence passes",
]
documents = ["openspec/specs/outbox/"]
+++

# CR-156: outbox send and outbox status

## Context

ADR-0020 decisions 4 and 5. `send`: after the check passes, stage only the
outbox — the outbox README's exclude pathspec applied the other way — and
make one batch commit; delivery stays with the operator. `status --index`:
hash each outbox file and compare with the `Source:` lines of an index file
the operator obtains; no network. CR-150 delivered `new` and `check`.

## Objective

An adopter sends a checked batch in one command and learns from an index
file which of their findings upstream has published.

## Acceptance Criteria

As in the header.

## Non-Goals

- Fetching the index from anywhere (the operator passes a file).
- Pushing or any delivery of the commit.
- Changes to `new`, to the check's rules, or to init's README.
