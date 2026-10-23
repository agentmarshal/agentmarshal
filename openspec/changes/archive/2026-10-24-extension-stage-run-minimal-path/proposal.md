## Why

The CR-211 contract amendment of 2026-10-24 resolved what criterion 3
left open: whether a `PATH` named in `isolation.env` passes the
caller's value through. It does not — the minimal `PATH` of
`/usr/bin:/bin` is always the core's, and the run's output says so
when a manifest names it. The code already does this and a test pins
it; the requirement's wording predates the amendment and is silent on
the one name the core keeps.

## What Changes

- The argv-process requirement names the value and the refusal: a
  minimal `PATH` of `/usr/bin:/bin` that the core always sets, and a
  `PATH` named in `isolation.env` not passed through with the run's
  output saying so.
- A new scenario pins the rule: a stage whose manifest names `PATH`
  sees the core's minimal value, not the caller's.

## Capabilities

- modify: `extension-stages`

## Impact

The specification catches up with the implemented behaviour: the
caller's `PATH` never reaches a stage, and the run says so once in its
output. No behaviour is added or removed by this delta alone.
