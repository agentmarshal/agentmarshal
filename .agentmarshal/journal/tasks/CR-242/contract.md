+++
schema = 2
id = "CR-242"
title = "The shared leak-scan acknowledgement mark says self-acknowledged where the acknowledging party is a declared writer, on every surface that prints it"
scope = [
  "src/agentmarshal/journal/capture.py",
  "src/agentmarshal/cli.py",
  "src/agentmarshal/journal/gate.py",
  "src/agentmarshal/journal/status_view.py",
  "src/agentmarshal/journal/report.py",
  "tests/",
  "openspec/changes/self-acknowledgement-mark/",
  "openspec/changes/archive/",
  "openspec/specs/leak-scan/",
]
acceptance = [
  "where an acknowledgement's acknowledging party matches a declared author or committer, the acknowledgement mark printed by `leak-scan` and by the gate says self-acknowledged in the terms status already uses, through the writer lookup and comparison CR-237 made shared (no second copy): the gate over the candidate range, `leak-scan` over the commit it scans (ADR-0021 decision 5; release-audit finding AUD-commands-3); the requirement states both conditions",
  "the change self-acknowledgement-mark carries a delta on the leak-scan capability (ADDED, or MODIFIED with full current text, heading byte for byte and every scenario) whose scenarios are each demonstrated by a test whose docstring names it; archived with the archive command (OpenSpec 1.15.0)",
  "an acknowledgement by any other party prints exactly as today; status's output is unchanged; existing transcript fixtures byte-identical; the suite and the full CI sequence pass",
]
documents = ["openspec/specs/leak-scan/"]
decisions = ["ADR-0021"]
+++

# Self-acknowledgement on the leak-scan mark

## Context

Release audit 0.6.0, area commands, finding AUD-commands-3: ADR-0021
decision 5 requires the acknowledgement mark to identify an
acknowledgement by the candidate's declared writer; only status compares
identities, while the shared mark `leak-scan` and the gate print carries
the actor and reason only. CR-237 made the writer lookup and comparison
shared for acceptances.

## Objective

Every surface that prints an acknowledgement says when it is a
self-acknowledgement.

## Acceptance Criteria

As in the header.

## Non-Goals

- Who may acknowledge; the acknowledgement records themselves.
