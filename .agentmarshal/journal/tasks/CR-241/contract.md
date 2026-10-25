+++
schema = 2
id = "CR-241"
title = "The outbox refuses a symlinked outbox or path component before any write, refuses a send whose staged bytes differ from the checked bytes, and outbox status escapes names"
scope = [
  "src/agentmarshal/outbox.py",
  "src/agentmarshal/project.py",
  "tests/",
  "openspec/changes/outbox-boundaries/",
  "openspec/changes/archive/",
  "openspec/specs/outbox/",
]
acceptance = [
  "`outbox new`, `outbox send` and the outbox initialization in `init` refuse, with one line naming the path, when `.agentmarshal/upstream` or any component between the project root and it is a symlink — before creating or writing anything — so a sidecar cannot write its host through a link (release-audit finding AUD-commands-1; docs/threat-model.md \"a sidecar never writes its host\"); tests on disk with a real symlink pointing outside the project",
  "`outbox send` refuses, naming the file, when the blob git would stage for a checked file differs from the hash of the bytes the leak scan read (e.g. a clean filter or eol conversion transforms it), so only checked bytes are committed (AUD-commands-2; outbox spec: the scan covers exactly what is sent); a test with a real git clean filter",
  "`outbox status` escapes every name it prints with the display-escaping helper the other outbox subcommands use (AUD-commands-6); a test with a control character in a file name",
  "the change outbox-boundaries carries a delta on the outbox capability (ADDED requirements, or MODIFIED with full current text, heading byte for byte and every scenario) with a scenario per behaviour above, each demonstrated by a test whose docstring names it; archived with the archive command (OpenSpec 1.15.0)",
  "an outbox with no symlink, no git transformation and printable names behaves and prints exactly as today; the suite and the full CI sequence pass",
]
documents = ["openspec/specs/outbox/"]
decisions = ["ADR-0020"]
+++

# Outbox boundaries

## Context

Release audit 0.6.0, area commands, findings AUD-commands-1 and -2
(blocking) and -6 (advisory): the outbox follows a symlinked directory
when it creates a draft or its README, so a sidecar's outbox linked into
the host writes the host, which the threat model forbids; the leak scan
reads raw bytes while staging applies git's clean filters, so a filter
can commit content the scan never saw; `outbox status` prints names
without escaping.

## Objective

The outbox writes only inside its own directory and commits only the
bytes it checked, and every name it prints is escaped.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any other outbox behaviour.
