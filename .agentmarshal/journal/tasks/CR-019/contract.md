+++
schema = 1
id = "CR-019"
title = "Ignore the whole .claude directory"
scope = [".gitignore"]
acceptance = []
+++

# CR-019: Ignore the whole .claude directory

## Context

First v2-native task after the self-hosting flip (dogfooding the v2 flow:
`open` -> implement -> `submit-review` -> `am-merge` -> `complete`). The
harness writes `.claude/settings.json` into the project during a session,
which repeatedly trips the clean-tree preflight (recurring class since
CR-005/016). `.gitignore` already ignores `.claude/settings.local.json`
but not the whole directory.

## Objective

Ignore the entire `.claude/` directory so harness-written files never
surface as untracked and break preflight.

## Acceptance Criteria

- [ ] `.gitignore` ignores `.claude/` (the whole directory), replacing
      the narrower `.claude/settings.local.json` entry.
- [ ] A stray `.claude/settings.json` no longer appears in
      `git status` as untracked.

## Non-Goals

- No other `.gitignore` changes; no code changes.
