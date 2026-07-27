+++
schema = 1
id = "CR-022"
title = "Gate CI-enforced attestation mode"
scope = ["src/agentmarshal/journal/gate.py", "src/agentmarshal/cli.py", "tests/test_gate.py"]
acceptance = []
+++

# CR-022: Gate CI-enforced attestation mode

## Context

The enforcement model is provider-specific (multi-provider strategy,
2026-07-27). For GitFlic there is no reliable "required pipeline for
merge", so the gate is invoked at merge and verifies pipeline
attestation itself (`pipeline_sha == commit`, Variant 1). GitHub has
native required status checks + branch protection, so the gate can run
as one required check among others (Variant 2): the provider blocks the
merge until every required check — the test check and the gate check —
is green, so the gate need not (and, running inside the same pipeline,
cannot honestly) self-attest that the tests passed. This slice adds an
explicit, opt-in attestation mode for that Variant-2 case, leaving the
default strict invoked behaviour unchanged so GitFlic is unaffected.

## Objective

`agentmarshal gate` supports an explicit `--attestation` mode so the
Variant-2 (provider-required-check) enforcement can delegate pipeline
attestation to the provider, while the default remains the strict
invoked attestation.

## Acceptance Criteria

- [ ] `agentmarshal gate --attestation commit` (the default) behaves
      exactly as today: it fails unless `pipeline_sha` equals the
      resolved commit.
- [ ] `agentmarshal gate --attestation ci-required` passes the
      attestation check without a `pipeline_sha`, emitting a PASS line
      that states attestation is delegated to the provider's required
      checks — usable only when the provider independently requires the
      test check for merge. All other gate checks are unchanged and still
      enforced.
- [ ] `run_gate` takes the mode as a parameter (default the strict
      commit mode); `complete` keeps the strict default. An unknown mode
      is a controlled `GateError`, never a traceback.
- [ ] The mode only affects the pipeline-attestation check; scope,
      review, independence, append-only, collision and lifecycle checks
      are untouched.
- [ ] Tests cover: default still refuses a missing/mismatched
      `pipeline_sha`; `ci-required` passes attestation without a
      `pipeline_sha` yet still refuses an unreviewed or out-of-scope
      candidate; an unknown mode raises `GateError`.
- [ ] `uv run agentmarshal validate`, `pytest`, `ruff check`,
      `ruff format --check`, `mypy` green locally and in CI.

## Non-Goals

- No GitHub Actions workflow, provider adapter, or branch-protection
  configuration (later Phase-A slices). No change to `complete`'s
  strict attestation or to `am-merge`. This slice is only the gate's
  attestation-mode seam.

