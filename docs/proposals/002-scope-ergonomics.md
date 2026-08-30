# 002 — Scope is silently accepted when it matches nothing

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.1.0 · **Disposition:** accepted

## Finding

`agentmarshal open --scope <directory>` written without a trailing slash creates
a contract that matches nothing. Scope entries are compared as directory
prefixes only when they end in `/`; otherwise they must equal a path exactly. A
task opened as `--scope src` therefore gates every file under `src/` as
out-of-scope, and nothing at open time says so.

The failure surfaces later, at the merge gate, on a change that is in fact
correct — the most expensive moment to discover it. Repairing it needs a second,
non-obvious step: the contract lives on the base side, so it must be amended
through its own journal-only transaction before the implementation can pass.

Adopter A also reports that `submit-review --commit` requires a full 40-character
SHA while the documentation shows abbreviated ones.

## Proposed

Warn at `open` time when a scope entry matches no path in the working tree;
document the trailing-slash rule where scope is introduced; accept an
abbreviated SHA or say plainly that the full one is required.

## Disposition — accepted

A silent no-op is the worst kind of misconfiguration: fail-closed gating is only
useful if the thing being enforced is what the author meant. The warning is
cheap and belongs at open time. Note that a warning is the right level, not a
refusal — a scope may legitimately name a path that does not exist yet.
