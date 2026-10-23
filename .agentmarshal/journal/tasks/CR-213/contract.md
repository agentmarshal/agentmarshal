+++
schema = 2
id = "CR-213"
title = "doctor lists the shared extensions with their form, stages, declared kinds and local grant state, and names a manifest it cannot read"
scope = [
  "src/agentmarshal/doctor.py",
  "tests/",
  "openspec/changes/doctor-extensions/",
  "openspec/changes/archive/",
  "openspec/specs/extension-manifest/",
]
acceptance = [
  "the change doctor-extensions has a proposal, a design.md and a delta spec on the capability extension-manifest with ADDED requirements; every scenario is demonstrated by a test whose docstring names it; the change is archived with the archive command",
  "`agentmarshal doctor` prints one section listing each shared extension found under `.agentmarshal/extensions/` of the working tree — its name, its form (file or directory), its manifest schema, its stages with their modes, its declared `ext` kinds — and, for a directory-form extension, its local grant state as `extension list` reports it (granted, not granted, changed after approval naming the file) by the same computation (CR-209)",
  "a manifest that cannot be read is named with the reason on one line and does not stop the rest of doctor; a project with no `.agentmarshal/extensions/` directory prints one line saying there are no extensions, and the rest of doctor's output is unchanged",
  "doctor's exit status and verdict follow its existing rules: an unreadable manifest is reported the way doctor reports its other malformed project settings; a missing grant is information, not a failure; every value is escaped on display",
  "doctor runs nothing an extension declares; no other command changes; the suite passes in CI's conditions and the full CI sequence passes",
]
documents = ["openspec/specs/extension-manifest/"]
decisions = ["ADR-0013"]
+++

# doctor: extensions

## Context

ADR-0013 decision 14 and section F give `doctor` the overview of
extensions: what is installed, what is granted, what changed. CR-152 and
CR-158 parse manifests in both forms, CR-209 keeps local grants and computes
whether a directory changed after approval. Checking dependencies against
their locks and the environment (runtimes) is a separate, larger task.

## Objective

One command shows a developer which extensions the project has and whether
their machine has approved them.

## Acceptance Criteria

As in the header.

## Non-Goals

- Dependencies against locks, runtimes, the environment (a later task).
- Personal and user-scope extensions (a later task).
- Running anything.
- Protection beyond what the published decisions promise (see
  docs/threat-model.md).
