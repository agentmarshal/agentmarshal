+++
schema = 2
id = "CR-120"
title = "OpenSpec 1.12.0 -> 1.13.2"
scope = [
  ".agentmarshal/extensions/openspec.toml",
  "openspec/",
  ".agents/skills/openspec-apply-change/",
  ".agents/skills/openspec-archive-change/",
  ".agents/skills/openspec-explore/",
  ".agents/skills/openspec-propose/",
  ".agents/skills/openspec-sync-specs/",
  ".agents/skills/openspec-update-change/",
  ".agents/skills/.openspec-target",
]
acceptance = [
  "the extension manifest names version 1.13.2 and its install command installs 1.13.2; its footprint, documents and artifacts are unchanged unless 1.13.2 writes a git-visible file outside the current footprint, in which case the footprint names it and the report says why",
  "the files under the footprint are exactly what the 1.13.2 install command writes over this repository, and nothing outside the footprint changes in git (the ignored .claude/ directory is not part of the candidate)",
  "`openspec validate --all --strict` with 1.13.2 passes over the existing baseline specs and archived changes",
  "the report summarises what changed between 1.12.0 and 1.13.2 from the package's release notes, and says, from a throwaway change created, validated and archived with 1.13.2 outside the worktree, whether archiving a new capability whose delta has no Purpose still writes a placeholder Purpose",
  "the full CI sequence passes",
]
decisions = ["ADR-0010"]
documents = ["openspec/specs/"]
+++

# CR-120: OpenSpec 1.12.0 -> 1.13.2

## Context

OpenSpec is this repository's first declared extension (ADR-0010), pinned at
1.12.0 since CR-090. Every task in the next stretch that changes behaviour goes
through an OpenSpec change, so the version should move before those tasks
start, not between them: a change created with one version and archived with
another is a second variable in every such task, and the procedure for
re-folding a baseline has been exercised on 1.12.0 only.

Three versions have been published since: 1.13.0, 1.13.1, 1.13.2 (2026-09-23)
and 1.14.0 (2026-09-30). This task takes 1.13.2, the latest patch of the 1.13
line; 1.14.0 is a day old.

## Objective

The repository runs OpenSpec 1.13.2, with its generated files, manifest and
validation in step, and the coordinator knows whether the archive behaviour it
relies on changed.

## Acceptance Criteria

As in the header.

## Non-Goals

- 1.14.0.
- Any change to a baseline spec's requirements or to an archived change.
- Any change in AgentMarshal's own behaviour.
