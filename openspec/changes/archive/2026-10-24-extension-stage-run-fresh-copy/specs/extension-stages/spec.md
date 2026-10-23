# extension-stages Specification (delta)

## MODIFIED Requirements

### Requirement: the extension's code is the base's and the working directory the candidate's

Each stage's extension directory SHALL be materialized from the merge
base's tree into a fresh temporary directory — each blob under
`.agentmarshal/extensions/<name>/` written byte for byte from `git
show`, a symbolic-link entry recreated as a link, a non-blob entry
refused as not materializable — and the stage's working directory
SHALL be a fresh temporary snapshot of the candidate commit produced
by `git archive`. The materialization and the snapshot SHALL be each
stage's own: no stage runs against a copy an earlier stage produced.
A materialized directory holding a symbolic link anywhere SHALL make
each of the extension's stages `not run (symlink in extension
directory: <path>)` — the refusal the grant hash gives on a
workstation, applied in CI too, where a linked intermediate directory
would otherwise put the command outside the approved copy. Neither
SHALL read the working tree, and the temporary directories SHALL be
removed when the command returns. A directory that cannot be
materialized SHALL make each of the extension's stages `not run`
naming why; a snapshot that cannot be materialized SHALL make that
stage `not run` naming why.

#### Scenario: the base commit's code runs, not the candidate's or the working tree's
- **WHEN** the candidate commit or the working tree carries a changed
  `bin/` script or a changed manifest
- **THEN** the stage that runs is the base commit's — the changed code
  and manifest play no part

#### Scenario: the working directory is a snapshot of the candidate commit
- **WHEN** a stage runs
- **THEN** its working directory holds the candidate commit's files and
  not the working tree's uncommitted or base-only contents

#### Scenario: an earlier stage cannot rewrite a later stage's command
- **WHEN** one extension declares two matching stages and the first
  stage rewrites the second stage's command inside its own
  materialized copy of the extension directory
- **THEN** the second stage still runs the base commit's command —
  each stage's materialization is its own

#### Scenario: a symbolic link inside the extension's directory is recreated as a link
- **WHEN** the base's extension directory contains a symbolic-link
  entry
- **THEN** the materialized directory holds a link at that path, and
  each of the extension's stages is `not run (symlink in extension
  directory: <path>)` — rather than a copy of whatever the working
  tree's link resolves to

#### Scenario: a gitlink inside the extension's directory is not run
- **WHEN** the base's extension directory contains a submodule entry
- **THEN** the extension's stages are `not run` naming why

#### Scenario: the temporary directories are gone when the command returns
- **WHEN** `stage run` finishes — checked, failed or paused
- **THEN** no materialized directory or snapshot remains
