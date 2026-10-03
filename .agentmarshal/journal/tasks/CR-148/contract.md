+++
schema = 2
id = "CR-148"
title = "One place resolves the clone's local state: the git common directory of the repository the journal lives in"
scope = [
  "src/agentmarshal/localstate.py",
  "src/agentmarshal/project.py",
  "tests/",
  "openspec/changes/local-state-location/",
  "openspec/changes/archive/",
  "openspec/specs/local-state/",
]
acceptance = [
  "the change local-state-location has a proposal, a design.md and a delta spec adding the local-state capability; every scenario in the delta spec is demonstrated by a test whose docstring names it; the change is archived with the archive command into openspec/specs/local-state/",
  "a function in src/agentmarshal/localstate.py returns `<git common directory>/agentmarshal/` for the repository that holds the project's journal, and named locations under it: `log/`, `extensions/`, `deps/`, `trust.toml`, `switches.toml`, `plan.toml`; a linked worktree resolves to the same directory as the main checkout; the git common directory is found by the existing helper in project.py, moved or exposed rather than copied",
  "in the sidecar placement the location is the journal repository's git common directory, never the host's: a test shows the host's working tree and git directory unchanged after resolving and creating every named location",
  "resolving never creates anything; a separate, explicit call creates a directory location when a writer needs it; where git cannot name the common directory the call fails with a message naming the repository and the cause, never a traceback",
  "nothing else in the tool uses the location yet, and the full CI sequence passes",
]
documents = ["openspec/specs/local-state/"]
+++

# CR-148: where local state lives

## Context

ADR-0014 decisions 4 and 5: the clone's local state — the process log,
personal extensions, dependencies, trust grants, switches, the plan file —
lives in the git common directory of the repository the work is in, under
`agentmarshal/`; in a sidecar, the journal repository's, because ADR-0008
promises the host is never written. ADR-0022 names the files. Several later
tasks write there; this one gives them one place to ask.

## Objective

One function says where local state lives, in every placement.

## Acceptance Criteria

As in the header.

## Non-Goals

- Writing any file there (the process log, trust and switches are later tasks).
- Printing the paths in status or doctor (a later task).
- The user scope directories (`~/.config/agentmarshal/` and the like).
