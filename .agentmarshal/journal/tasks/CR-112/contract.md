+++
schema = 1
id = "CR-112"
title = "Master carries the next version as a development release"
scope = [
  "pyproject.toml",
  "uv.lock",
  "src/agentmarshal/__init__.py",
  "tests/test_smoke.py",
  "CONTRIBUTING.md",
  ".github/workflows/release.yml",
]
acceptance = [
  "the package version is 0.5.0.dev0 in pyproject.toml, src/agentmarshal/__init__.py and uv.lock, and `agentmarshal --version` prints it",
  "CONTRIBUTING.md states the versioning rule: the default branch carries the next release's version with a .dev0 suffix, the release task removes the suffix, and the task after the tag restores it for the following release",
  "the release workflow refuses to publish a version that is a development or local version, before it builds anything, in addition to its existing tag check",
  "the tests that pin the published 0.3.0 transcript pass with their expectations unmodified, and the full CI sequence passes",
]
+++

# CR-112: master carries the next version as a development release

## Context

A build from the default branch reported the same version as the latest
release while differing from it by more than a hundred commits. An adopter
could not tell which set of promises applied (proposal 016), and this
repository's own tests have to tell the published 0.3.0 from a build of the
default branch by probing for a command instead of reading the version.
0.4.0 has just been published.

## Objective

Anything built from the default branch between releases reports a version
that sorts after the last release and before the next one, and says it is a
development build.

## Acceptance Criteria

As in the header.

## Non-Goals

- Deriving the version from git (a commit hash in the version). That needs a
  different build backend; it is a separate decision.
- Any change in behaviour, and any CHANGELOG entry: the changelog describes
  published releases.
- Changing how the 0.3.0 transcript tests locate the published release.
