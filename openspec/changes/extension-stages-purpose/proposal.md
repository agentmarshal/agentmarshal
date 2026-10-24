## Why

The `extension-stages` capability's `## Purpose` still describes the
capability's first wave: it ends by calling network isolation, write
isolation and pause records later work. That work has since landed in
the spec's own requirements — the user/network namespace floor and the
read-only pre-gate candidate (extension-stage-isolation), the switches
file and the operational lane (extension-switches, extension-switch-off),
the accepted pause (extension-accepted-pause) and `complete` invoking
the same runner before its gate check and after `completed` is written
(complete-runs-stages). The first paragraph a reader opens says none of
it exists.

## What Changes

The capability's `## Purpose` is rewritten to describe what its
requirements already say: the base's manifests, code and switches; the
workstation grant; a switched-off extension's result line; the declared
isolation enforced where the platform allows and named where it is not;
the accepted pause standing a `pre-gate-stop` pause down; and
`complete` running the `pre-gate` stages before its gate check — a
pause refusing while the candidate is not merged into `--target` — and
the `post-gate` stages after `completed`. No requirement changes.

## Capabilities

- modify: `extension-stages`

## Impact

Documentation only — the delta carries `## Purpose` and no requirement
section. If the archive command refuses a delta with no requirement
change, the refusal is reported and no spec file is edited by hand.
