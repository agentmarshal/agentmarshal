## Why

[ADR-0014](../../../../docs/adr/ADR-0014-where-things-live.md) decisions 4 and 5
place the clone's local state — the process log, personal extensions,
installed dependencies, trust grants and personal switches — in `agentmarshal/`
under the git common directory of the repository the work is in; in a sidecar,
of the journal repository, because
[ADR-0008](../../../../docs/adr/ADR-0008-journal-placements.md) promises the host
is never written.
[ADR-0022](../../../../docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md)
section 7 adds the plan file to the same directory. Several coming tasks write
there — the process log, the trust and switch files, the plan file — and each
would otherwise derive the location on its own. Getting it wrong in a sidecar
is not a cosmetic defect: it writes the host.

## What Changes

One module, `localstate.py`, answers "where": resolving a placement yields
`<git common directory>/agentmarshal/` and the six named locations under it.
The common directory comes from the one existing helper in `project.py`,
exposed rather than copied. Resolving creates nothing; a separate explicit
call creates a directory location when a writer needs it. Nothing calls the
module yet — the writers are later tasks.

## Capabilities

- new: `local-state`

## Impact

A linked worktree resolves to the same place as the main checkout; a sidecar
resolves to the journal repository's git directory, never the host's. Where
git cannot name the common directory the caller fails with a message naming
the repository and the cause, not a traceback.
