# operational-skip-ext-refusal — Design

## Context

Finding SOL-docs-claims-1-1 of the gpt-6.1-sol measurement audit: the
spec's operational-lane exception — one line, success, before any
manifest is read — was taken before the `--skip-ext` shared-name
refusal, so the lane accepted a flag every other lane refuses. The
implementation now refuses a shared name in `--skip-ext` first, on the
names the merge base's `.agentmarshal/extensions/` enumerates —
`_extension_names_at_tree`, the enumeration the gate's own lane
predicate shares — reading no manifest for it, and only then asks the
operational-lane predicate.

## Decision

The requirement keeps its heading byte for byte and every scenario, and
its exception sentence gains the ordering: the `--skip-ext` refusal of a
shared name precedes the exception, decided on the enumerated names
alone, as "a shared extension is never named in a personal switch"
states. One scenario records it: a shared name in `--skip-ext` on an
operational candidate prints the refusal line — not the operational
line — and no manifest is read and no stage is planned. The gate-lanes
requirement that states the same operational pre-gate line takes the
matching MODIFIED block: the same ordering, the same added scenario.

## Risks / Trade-offs

- The enumeration still reads the base tree's `extensions/` listing —
  names only, never manifest content — so a broken extension's manifest
  still cannot block its own switching off (ADR-0013 decision 17); the
  scenario's fixture carries a broken manifest to pin that.
