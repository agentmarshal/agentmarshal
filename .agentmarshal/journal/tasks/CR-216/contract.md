+++
schema = 2
id = "CR-216"
title = "doctor finds a wrapper extension's declared runtime on PATH and names its path and version against the declared minimum"
scope = [
  "src/agentmarshal/doctor.py",
  "tests/",
  "openspec/changes/doctor-wrapper-runtime/",
  "openspec/changes/archive/",
  "openspec/specs/extension-manifest/",
]
acceptance = [
  "the change doctor-wrapper-runtime has a proposal, a design.md and a delta spec on the capability extension-manifest with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "for each shared extension whose manifest declares `[wraps]`, `doctor` looks up the runtime's `<name>` on `PATH` (the one PATH exception, ADR-0013 decision 13 as amended), runs it with `--version` under a short time limit, never through a shell, and prints the path found, the version it reports and whether that meets the declared minimum `<name> >= <version>`",
  "versions are compared by their leading numeric dot-separated components (a leading `v` ignored), and a version that cannot be read so is reported as unreadable rather than guessed; a runtime not found on PATH, one that fails or does not answer in time, and one below the minimum are each reported on the extension's line by doctor's existing rules for a failed check",
  "an extension without `[wraps]` gets no runtime line, and a project without wrappers prints doctor's output of today plus nothing; every value is escaped on display",
  "doctor runs nothing an extension declares and installs nothing; no other command changes; tests do not depend on what is installed on the machine (they put a fake runtime on a temporary PATH); the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-manifest/"]
decisions = ["ADR-0013"]
+++

# doctor: a wrapper's runtime

## Context

ADR-0013 decision 13, as amended on 2026-10-03: the one exception to the
`PATH` ban is the runtime a wrapped product needs — `node` for a JavaScript
product; the manifest declares its name and a minimum version, the core
finds it on `PATH`, and `doctor` and the stage output name the path and
version found. CR-152 parses `[wraps].runtime` as `<name> >= <version>`;
CR-213 gave `doctor` its extensions section. Checking installed
dependencies against their locks is a separate task.

## Objective

A developer sees, before any stage runs, whether the runtime a wrapper
needs is present and new enough.

## Acceptance Criteria

As in the header.

## Non-Goals

- Dependencies against locks (a later task); installing anything.
- The stage runner using the runtime (with the wrapper extension itself).
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
