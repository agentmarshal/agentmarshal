+++
schema = 2
id = "CR-247"
title = "The default branch carries 0.7.0.dev0 after the 0.6.0 release"
scope = [
  "pyproject.toml",
  "uv.lock",
  "src/agentmarshal/__init__.py",
  "tests/test_smoke.py",
]
acceptance = [
  "the package version is 0.7.0.dev0 in pyproject.toml, src/agentmarshal/__init__.py and uv.lock, the smoke test asserts it, and `agentmarshal --version` prints it",
  "no other file changes; no statement about 0.6.0 as history changes; the full CI sequence passes",
]
documents = []
decisions = ["ADR-0001"]
+++

# 0.7.0.dev0

## Context

0.6.0 is released (tag v0.6.0, PyPI, GitHub Release). The default branch
carries the next development version so a branch build cannot be mistaken
for the release, as after 0.5.0 (CR-205).

## Objective

master says 0.7.0.dev0.

## Acceptance Criteria

As in the header.

## Non-Goals

- Any 0.7.0 work.
