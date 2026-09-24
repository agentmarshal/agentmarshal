+++
schema = 1
id = "CR-115"
title = "Release 0.4.1"
scope = [
  "CHANGELOG.md",
  "UPGRADING.md",
  "pyproject.toml",
  "uv.lock",
  "src/agentmarshal/__init__.py",
  "tests/test_smoke.py",
]
acceptance = [
  "CHANGELOG.md has a 0.4.1 section dated the day of the release in which every entry names the task it comes from and describes only merged behaviour; the three tasks landed since v0.4.0 — CR-112, CR-113, CR-114 — each appear, and the entry for the fix says what an installation that hit the refusal does",
  "UPGRADING.md's section about the refused review record is headed as the 0.4.0 -> 0.4.1 step and states that nothing else in it requires action",
  "the package version is 0.4.1 in pyproject.toml, src/agentmarshal/__init__.py and uv.lock, and `agentmarshal --version` prints it",
  "no statement names a release, task or document that is not published, and no statement about 0.4.0 as history is changed",
  "the full CI sequence passes; the release candidate's own validate runs read-only over the journal of the adopter that reported the defect and passes there too, and the run is reported in the task's completion",
]
+++

# CR-115: release 0.4.1

## Context

0.4.0 was published on 2026-09-18. An adopter on a pinned 0.3.0 ran its
`validate` over their journal before upgrading and it refused two review
records an earlier release had written, over a narrow no-break space. The
upgrade was blocked: their CI validates the whole journal, and the records of a
closed task cannot be repaired. CR-114 narrowed the rule to the characters that
can add a line, reorder text or fail to encode, and the fix is verified against
that adopter's journal.

Three tasks landed since the tag: CR-112 (the default branch carries the next
version as a development release, and the release workflow refuses to publish
one), CR-113 (the intake of proposal 024 and the documentation that token counts
are not what a provider charges), and CR-114 (the fix).

## Objective

0.4.1 is published, and an installation that hit the refusal learns from the
release notes that this is the release to move to.

## Acceptance Criteria

As in the header.

## Non-Goals

- Publishing. Pushing the version tag triggers the release workflow and uploads
  to PyPI; that is an outward action the operator authorises after this task
  lands.
- Any change in behaviour, and any new entry in the 0.4.0 section.
- Restoring the development version on the default branch: the first task after
  the tag does that, as CONTRIBUTING says.
