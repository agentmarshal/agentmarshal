## 1. The delta

- [x] 1.1 `specs/extension-stages/spec.md` carries the rewritten
  `## Purpose` — the base's manifests, code and switches; the
  workstation grant; a switched-off extension's result line; the
  declared isolation enforced where the platform allows and named where
  it is not; the accepted pause standing a `pre-gate-stop` pause down;
  `complete` at both points — and no longer calls network isolation,
  write isolation or pause records later work — verify: the Purpose
  describes what the published requirements already say.
- [ ] 1.2 `openspec validate extension-stages-purpose --strict` passes
  — verify: the validator reports the change valid.
- [ ] 1.3 The change is archived with the archive command — verify: it
  lives under `openspec/changes/archive/` and the capability's
  `## Purpose` is updated by it; if the archive command refuses a delta
  with no requirement change, the refusal is reported and no spec file
  is edited by hand.
