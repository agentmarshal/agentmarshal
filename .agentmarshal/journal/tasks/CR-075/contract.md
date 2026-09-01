+++
schema = 1
id = "CR-075"
title = "Release 0.2.0: date the changelog entry"
scope = ["CHANGELOG.md"]
acceptance = [
  "the 0.2.0 heading carries the UTC date the release is tagged, not `unreleased`",
  "the date is the UTC date at tagging, and is reconciled against the index once the upload exists",
  "nothing else in the changelog changes",
]
+++

# CR-075: Release 0.2.0 — date the changelog entry

## Context

Everything for 0.2.0 is in place: the version, the changelog, the upgrade guide,
the documentation audit and a quickstart verified against a wheel built from
this source. One thing is left that belongs in the repository rather than in the
release machinery — the changelog entry still reads `unreleased`.

Publishing itself is a tag push. The workflow verifies that the tag matches the
project version and uploads through Trusted Publishing; PyPI versions are
immutable, so the tag is the point of no return.

## Objective

Date the entry, so the artifact that ships does not describe its own version as
unreleased.

## Acceptance Criteria

- The `## 0.2.0` heading carries the UTC date on which the release is tagged,
  in place of `unreleased`.
- The date is the **UTC date at tagging**. It cannot be the upload date at the
  moment it is written, because the upload has not happened — the entry is a
  prediction until the tag is pushed, and is reconciled against the index
  immediately afterwards. Where the two differ, the index wins and the entry is
  corrected: the file's convention says dates are the index's.
- Nothing else in the changelog changes.

## Threat model and boundaries

One line in one document, and no behaviour.

What deserves care is not the edit but its **timing**: the date is a prediction
until the upload happens. It is written immediately before tagging, and checked
against the index afterwards. If the upload lands on a different UTC day than
the tag, the entry is corrected — the file's own convention says the date is the
index's, so the index is what settles it.

## Non-Goals

- Changing anything else about the release, the workflow, or the version.
- Announcing the release anywhere.
- Deciding whether to publish. That decision is the operator's and has been
  given.
