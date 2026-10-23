## Why

The extension-stages delta left two things unsaid that the run already
does. Each stage gets its own fresh materialization of the extension
directory and its own fresh snapshot of the candidate — a stage can
reach its materialized copy through `__file__`, so a shared copy would
let one stage rewrite a later stage's command — but no requirement or
scenario says so. And a materialized directory holding a symbolic link
anywhere is refused before the grant is consulted, in CI as on a
workstation, while the archived wording still ascribed that refusal to
the workstation's grant hash alone.

## What Changes

- The materialization requirement gains the per-stage rule — each
  stage's own fresh extension-directory copy and candidate snapshot —
  and the refusal `not run (symlink in extension directory: <path>)`
  for a materialized directory holding a link anywhere.
- A new scenario pins the freshness: an earlier stage cannot rewrite a
  later stage's command in a shared copy.
- The symbolic-link scenario is reworded to the refusal the run gives,
  on a workstation and in CI alike.

## Capabilities

- modify: `extension-stages`

## Impact

The specification catches up with the implemented behaviour: the code
that runs is the base's, each stage's copies are its own, and the link
refusal is the grant hash's own, extended to CI. No behaviour is added
or removed by this delta alone.
