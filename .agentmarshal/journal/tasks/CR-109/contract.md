+++
schema = 2
id = "CR-109"
title = "Release 0.4.0"
scope = [
  "CHANGELOG.md",
  "UPGRADING.md",
  "README.md",
  "pyproject.toml",
  "uv.lock",
  "src/agentmarshal/__init__.py",
  "docs/",
  ".github/workflows/agentmarshal-governance.yml",
  "tests/",
]
acceptance = [
  "CHANGELOG.md has a 0.4.0 section dated 2026-09-18 in which every entry names the task or tasks it comes from, describes only merged behaviour, says where a capability is partial, and points the reader at nothing they cannot open — no 'planned', 'next', 'in line' or 'soon' about anything not in a published document",
  "UPGRADING.md's 0.3.0 -> 0.4.0 section names every change that affects an existing installation, including that record schemas 4, 5 and 6 are introduced in this release so 0.3.0 cannot read a journal containing any of them, that writers now refuse a record the projection would refuse to read, that a reopening transaction now lands, the gate's review-free mode and the template change that uses it, and the leak-scan output change",
  "the package version is 0.4.0 in pyproject.toml, src/agentmarshal/__init__.py and uv.lock, and `agentmarshal --version` prints it",
  "every statement about 'the current release' names 0.4.0, every statement about 0.3.0 as history keeps 0.3.0, and the tests that pin the published 0.3.0 transcript byte for byte pass with their expectations unmodified",
  "the three advisory findings left by the documentation task are resolved: the roadmap section of docs/overview.md does not list a direction under a heading that says designed, proposal 005 points at nothing unpublished, and the governance job in this repository's workflow keeps the template's comment",
]
+++

# CR-109: release 0.4.0

## Context

Twenty-five tasks have landed since 0.3.0 (CR-084 to CR-108). The changelog has
no 0.4.0 section; the upgrade guide has one entry of the several a 0.3.0
installation needs to know about; the version still reads 0.3.0. Three of the
landed tasks fix defects in behaviour 0.3.0 shipped — a writer that could leave
a journal unreadable, a reopening that could not merge, a findings lane with no
launcher — and three introduce record schemas 0.3.0 cannot read.

## Objective

A reader of the changelog and the upgrade guide knows what 0.4.0 does and what
upgrading requires, and the package says it is 0.4.0.

## Acceptance Criteria

See the `acceptance` field above.

## Non-Goals

- Publishing. Pushing the version tag triggers the release workflow and uploads
  to PyPI; that is an outward action the operator authorises after this task
  lands, not part of it.
- GitHub Releases, repository settings, and announcements.
- Any change in behaviour.
