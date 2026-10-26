# operational-skip-ext-refusal

## Why

The invocation requirement's operational-lane exception said the run
prints one line and returns success before any manifest is read — which
placed it ahead of the `--skip-ext` refusal a shared name draws on every
other lane: on a candidate the operational lane admits, `stage run
--phase pre-gate --skip-ext <shared>` printed the operational line and
exited 0, while the same flag off the lane refuses as "a shared
extension is never named in a personal switch" states. A measurement
audit (gpt-6.1-sol, docs-claims area, finding SOL-docs-claims-1-1)
confirmed the divergence at master; the fix moved the shared-name
refusal — decided on the names the base's `extensions/` enumerates, no
manifest read — ahead of the lane's early return, and this change states
that ordering in the spec.

## What Changes

- The invocation requirement's operational-lane exception now follows
  the `--skip-ext` refusal: a shared name is refused first — on the
  enumerated names alone, no manifest read — and only then does the
  exception apply. One scenario added; the heading and every other
  scenario are unchanged.

## Capabilities

- modified: `extension-stages`

## Impact

Specification only — the code and tests landed with the fix.
`openspec/changes/archive/` and `openspec/specs/extension-stages/spec.md`
change only through the archive command.
