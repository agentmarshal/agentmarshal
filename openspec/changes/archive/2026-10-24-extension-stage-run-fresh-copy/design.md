## Context

The extension-stages review found the per-stage freshness of the
materialization and the snapshot unspecified: the design note records
it and the tests pin it, but no requirement or scenario does. The same
review fixed what a symbolic link inside the materialized directory
draws — a refusal of the stage itself, `not run (symlink in extension
directory: <path>)`, the grant hash's own refusal extended to CI —
which the archived wording still ascribed to the workstation's grant
hash alone.

## Decisions

- The materialization requirement carries the rule itself rather than
  leaving it to design prose: an extension's stage can reach its
  materialized copy through `__file__`, so a shared copy would let one
  stage rewrite another's command — each stage's copy and snapshot is
  its own.
- The link refusal is stated where materialization is: any link the
  materialized directory holds makes each of the extension's stages
  `not run (symlink in extension directory: <path>)`, on a workstation
  and in CI alike.
