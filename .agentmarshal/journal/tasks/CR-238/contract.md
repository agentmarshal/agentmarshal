+++
schema = 2
id = "CR-238"
title = "The personal-extension authority requirement and the release notes say what the core enforces: no journal write path through the core, not containment of the extension's process"
scope = [
  "openspec/changes/personal-authority-wording/",
  "openspec/changes/archive/",
  "openspec/specs/extension-stages/",
  "CHANGELOG.md",
  "UPGRADING.md",
]
acceptance = [
  "the change personal-authority-wording carries a MODIFIED block (full current text, heading byte for byte, every scenario) for the extension-stages requirement \"a personal extension has no journal authority\": the requirement states what the core enforces — a personal extension has no `ext` kind `record-ext` accepts, no footprint, documents or artifacts, and no effect on the gate or the server-side process — and says that its process runs with the developer's rights and is not contained beyond the stage isolation, as docs/threat-model.md states (release-audit finding AUD-extensions-1); no SHALL in it promises that the process writes nothing to the journal; archived with the archive command (OpenSpec 1.15.0)",
  "CHANGELOG.md's 0.6.0 personal-extensions paragraph and UPGRADING.md's personal-extensions bullet no longer state as enforced that a personal extension writes to no shared surface or never reaches the journal; they say it has no write path into the journal through the core and that the threat model's same-user caveat applies",
  "no code changes; every other statement unchanged; the suite and the full CI sequence pass",
]
documents = ["openspec/specs/extension-stages/", "CHANGELOG.md", "UPGRADING.md"]
decisions = ["ADR-0013"]
+++

# Personal-extension authority: what is enforced

## Context

Release audit 0.6.0, area extensions, finding AUD-extensions-1: the
requirement "a personal extension has no journal authority" says a
personal extension SHALL write nothing to the journal, and the release
notes say it writes to no shared surface and never reaches the journal.
The core enforces only the absence of a write path through itself
(record-ext kinds, footprint); the extension's process runs with the
developer's rights, which ADR-0013 decision 15 and docs/threat-model.md
state plainly. The promise must say what holds.

## Objective

The specification and release notes claim no containment the core does
not enforce.

## Acceptance Criteria

As in the header.

## Non-Goals

- Enforcing a write boundary for personal stages (a later decision).
