+++
schema = 1
id = "CR-205"
title = "The default branch carries 0.6.0.dev0 after the 0.5.0 release"
scope = [
  "pyproject.toml",
  "uv.lock",
  "src/agentmarshal/__init__.py",
  "tests/test_smoke.py",
]
acceptance = [
  "the package version is 0.6.0.dev0 in pyproject.toml, src/agentmarshal/__init__.py and uv.lock, the smoke test asserts it, and `agentmarshal --version` prints it",
  "no other file changes; no statement about 0.5.0 as history changes; the full CI sequence passes",
]
+++

# The default branch carries 0.6.0.dev0

## Context

0.5.0 was tagged and published to PyPI on 2026-10-23 (upload 14:00 UTC)
from the merge of CR-204. CONTRIBUTING's rule (CR-112): between releases
the default branch carries the next version with a `.dev0` suffix, so a
build from it never reports a published release's version; the release
workflow refuses to publish a development version. CR-116 did the same
after 0.4.1.

## Objective

A build from the default branch reports a version that is not a release.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any change of behaviour, documentation or release notes.
