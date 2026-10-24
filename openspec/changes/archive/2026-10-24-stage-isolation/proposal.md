## Why

ADR-0013 decision 8 declares what stages may reach: the manifest's
`isolation` section declares `network`, `env` and `writes`, and at
`pre-gate` a floor stands that the manifest cannot remove — the
candidate snapshot is read-only and provider secrets never reach the
stage. Until now nothing enforced any of it: the environment contract
kept declared names out, but the stage's process shared the caller's
network and could write the candidate it was checking. The
`extension-stages` capability's own Purpose still calls this later
work; this change is the work.

## What Changes

- A stage whose manifest declares no `network = true` runs in a new
  user and network namespace — `os.unshare` in the stage's own child
  after `fork` and before `execve`, with the identity uid/gid maps —
  never a wrapper process or a shell.
- At `pre-gate`, a mount namespace in the same child binds the
  candidate directory read-only over itself — `MS_REC | MS_PRIVATE`
  on `/`, a self-bind, a `MS_BIND | MS_REMOUNT | MS_RDONLY` remount.
- In the same child, before `execve`, every capability the new user
  namespace granted is dropped — the ambient set, the `NOROOT`/
  `NO_SETUID_FIXUP` securebits and `no_new_privs`, the bounding set
  and the live capability sets — because they otherwise survive
  `execve` (user_namespaces(7)) and let the stage undo the
  enforcement for any uid. A drop that fails names every guarantee
  the child was asked to enforce; the stage still runs.
- At `pre-gate`, provider secrets — a fixed list plus the
  `_API_KEY`/`_TOKEN`/`_SECRET`/`_PASSWORD` suffixes — are withheld
  even when `isolation.env` names them; `post-gate` is unchanged.
- A run-scoped probe in a throwaway child answers once which
  guarantees this platform and environment allow. What cannot be
  enforced is named on a note line per stage — `not enforced:
  <guarantee> (<reason>)` — the stage still running; what is
  enforced is not mentioned. A declared `writes` beyond the
  candidate is always named — the core has no filesystem sandbox
  there. A setup step that fails in the stage's own child reports
  itself before exec and is named the same way.

## Capabilities

- modify: `extension-stages`

## Impact

Stages can no longer silently reach the network or rewrite the
candidate they check; where the platform cannot enforce that, the
run says so honestly instead of weakening the guarantee silently.
Result-line formats, switched-off and not-run behaviour, the grant
flow and every other command are unchanged.
