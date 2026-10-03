# local-state Specification

## Purpose
Where the clone's local state lives — the process log, personal extensions,
installed dependencies, trust grants, personal switches and the plan file.
ADR-0014 decisions 4 and 5 place it in `agentmarshal/` under the git common
directory of the repository that holds the project's journal; one function
gives every later writer the same answer, in every placement.

## Requirements

### Requirement: The local state root is the journal repository's git common directory

Resolving a project's local state SHALL return `agentmarshal/` under the git
common directory of the repository that holds the project's journal. In the
embedded placement that is the project's own repository; in a sidecar it is
the journal repository — never the host's, whose working tree and git
directory SHALL NOT be written. Every worktree of one repository SHALL
resolve to the same root, so a linked worktree shares the main checkout's
local state.

The git common directory SHALL be named by git itself — one helper asking
`git rev-parse` — not derived from the worktree's layout, which differs
between a checkout, a linked worktree and a separated git directory.

#### Scenario: an embedded project resolves under its own git directory
- **WHEN** local state is resolved for an embedded placement
- **THEN** the root is the project's git common directory joined with
  `agentmarshal/`

#### Scenario: a linked worktree resolves to the shared location
- **WHEN** local state is resolved from a linked worktree of a repository
- **THEN** the root is the same directory the main checkout resolves to

#### Scenario: a sidecar resolves to the journal repository's git directory
- **WHEN** local state is resolved for a sidecar placement
- **THEN** the root is the journal repository's git common directory joined
  with `agentmarshal/`, not the host's

### Requirement: The named locations under the root

The module SHALL name the locations the map of places fixes: the `log/`,
`extensions/` and `deps/` directories and the `trust.toml`, `switches.toml`
and `plan.toml` files, each a path under the resolved root, so no writer
spells them for itself.

#### Scenario: every named location sits under the root
- **WHEN** a local state root has been resolved
- **THEN** it names `log`, `extensions`, `deps`, `trust.toml`,
  `switches.toml` and `plan.toml`, each directly under the root

### Requirement: In a sidecar, nothing reaches the host

Resolving and creating every named location in a sidecar placement SHALL
leave the host's working tree and git directory untouched.

#### Scenario: the host is unchanged after resolving and creating every location
- **WHEN** local state is resolved for a sidecar and every named location is
  created
- **THEN** the host's working tree and its git directory are byte-for-byte
  what they were before

### Requirement: Resolving creates nothing; creating is explicit

Resolving local state SHALL NOT create any directory or file. Creating a
directory location SHALL be a separate call a writer makes when it needs the
directory to exist.

#### Scenario: resolving leaves no trace on disk
- **WHEN** local state is resolved
- **THEN** neither the root nor any named location exists afterwards

#### Scenario: a writer creates a directory location explicitly
- **WHEN** a writer asks for a directory location to be created
- **THEN** that directory exists, along with any missing parents

### Requirement: Failure names the repository and the cause

Where git cannot name the repository's common directory, resolving SHALL
fail with a message naming the repository and the cause — never a traceback
or a bare exit status.

#### Scenario: a project outside git fails cleanly
- **WHEN** local state is resolved for a project whose root is inside no git
  worktree
- **THEN** the failure names the repository's path and git's reason

### Requirement: Local state needs git 2.31 or newer, and `doctor` says so

The helper asking `git rev-parse` asks it with
`--path-format=absolute` — a flag git learned at 2.31 — so resolving
local state requires git 2.31 or newer. `doctor`'s git check SHALL
name that minimum and what it is needed for, and SHALL fail with the
remedy — upgrade git — in the message when the installed git is older
or its version cannot be read. The version SHALL be parsed from `git
--version` output as its first dotted number, so a platform suffix —
`.windows.1`, `(Apple Git-…)`, a vendor's own — plays no part.

#### Scenario: an older git fails the check naming the minimum and the remedy
- **WHEN** `git --version` reports a version older than 2.31
- **THEN** `doctor`'s git check fails, naming 2.31 as the minimum
  local state needs and upgrade git as the remedy

#### Scenario: a new-enough git passes the check
- **WHEN** `git --version` reports version 2.31 or newer
- **THEN** `doctor`'s git check reports the executable available

#### Scenario: the version parses without its platform suffix
- **WHEN** `git --version` reports a version carrying a platform
  suffix, such as `2.39.2.windows.1`
- **THEN** the check reads the version and judges it against the
  minimum, the suffix playing no part

#### Scenario: a version that cannot be read fails the check
- **WHEN** `git --version` succeeds but names no dotted version
- **THEN** `doctor`'s git check fails, naming the minimum local state
  needs and the remedy
