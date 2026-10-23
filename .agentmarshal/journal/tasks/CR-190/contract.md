+++
schema = 2
id = "CR-190"
title = "leak-scan prints an acknowledged hit marked with who acknowledged it and why, and exits 1 only on a hit nobody acknowledged"
scope = [
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/capture.py",
  "tests/",
  "openspec/changes/leak-scan-honours-acknowledgements/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
]
acceptance = [
  "the change leak-scan-honours-acknowledgements has a proposal, a design.md and a delta spec on the capability leak-scan with ADDED requirements (and MODIFIED where the existing exit-status requirement changes); every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal leak-scan --base --commit` reads the `acknowledgement` records whose `commit` equals the resolved candidate commit — from every task of the journal, or from one task when an optional `--task <id>` is given — and a hit is acknowledged when a record carries the same file, exactly as the scan prints it, and the same identification (signature id or marker number), as ADR-0021 decision 2 binds",
  "every hit is still printed, in today's order and form; an acknowledged hit's line additionally carries a mark naming who acknowledged it and the reason, escaped on display; nothing is removed, and the matched text is never printed",
  "the command exits 0 when the scan finds hits and every one is acknowledged, 1 when any hit is unacknowledged, and as today when the scan finds nothing; when the journal or a task's records cannot be read, no hit counts as acknowledged and the command says why on stderr",
  "the gate's leak-scan line and its bound are unchanged by this task (marking there is a later task); no other command changes; the gate's fixtures and every documented transcript a test pins are unchanged; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/leak-scan/"]
decisions = ["ADR-0021", "ADR-0022"]
+++

# leak-scan honours acknowledgements

## Context

ADR-0021 decision 3: an acknowledgement never removes a hit from a surface
that shows it; the command prints every hit, an acknowledged one marked —
acknowledged, by whom, and the reason — and what changes is the exit
status: an acknowledged hit no longer makes `leak-scan` exit 1, while a hit
nobody acknowledged still does. Decision 2: a record matches a hit only on
the same commit, file and identification, so a new commit or a renumbered
marker shows the hit again as unacknowledged. CR-170 landed the record and
CR-187 the `acknowledge` command that writes it after checking the hit
against the same scan.

The scan takes no task today; an acknowledgement is bound to a commit, so
reading every task's acknowledgements for that commit finds the right ones
without guessing a task from a branch name.

## Objective

An operator who has acknowledged every hit on a candidate gets a clean exit
from the scan, and still sees every hit.

## Acceptance Criteria

As in the header.

## Non-Goals

- The gate printing the mark on its leak-scan line (a later task).
- Self-acknowledgement marking in the command's output (`status` carries it
  since CR-184).
- Any change to what the scan matches.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
