# personal-authority-wording

## Why

Release audit 0.6.0, area extensions, finding AUD-extensions-1: the
requirement "a personal extension has no journal authority" says a
personal extension SHALL write nothing to the journal, and the release
notes say it writes to no shared surface and never reaches the journal.
The core enforces only the absence of a write path through itself —
`record-ext`'s accepted-kind set and the personal manifest's refused
fields — while the extension's process runs with the developer's
rights, which ADR-0013 decision 15 and docs/threat-model.md state
plainly. The promise must say what holds.

## What Changes

- The extension-stages requirement "a personal extension has no journal
  authority" is restated as what the core enforces — `record-ext`
  accepts only kinds a shared extension declares, the manifest carries
  no `footprint`, `documents` or `artifacts`, no personal stage affects
  the gate or the server-side process, and `extension-event`s carry
  `scope` `personal` — and states the same-user caveat in place of a
  containment no enforcement provides. The heading and every scenario
  are unchanged.
- `CHANGELOG.md`'s 0.6.0 personal-extensions paragraph and
  `UPGRADING.md`'s personal-extensions bullet say a personal extension
  has no write path into the journal through the core and that the
  threat model's same-user caveat applies, rather than that it writes
  to no shared surface or never reaches the journal.

## Capabilities

- modified: `extension-stages`

## Impact

Specification and release notes only — no code changes.
`openspec/changes/archive/` and `openspec/specs/extension-stages/spec.md`
change only through the archive command.
