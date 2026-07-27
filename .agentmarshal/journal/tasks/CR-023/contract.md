+++
schema = 1
id = "CR-023"
title = "GitHub Actions governance workflow template"
scope = ["templates/github/agentmarshal-governance.yml", "docs/github-enforcement.md"]
acceptance = []
+++

# CR-023: GitHub Actions governance workflow template

## Context

Multi-provider strategy (2026-07-27): GitHub is the intended home and a
first-class governance target, where enforcement is Variant 2 — the gate
runs as a required status check and branch protection blocks the merge
until every required check is green (enabled by CR-022's `ci-required`
attestation mode). This slice ships the GitHub-side artifacts: an Actions
workflow template plus a setup doc.

Honest boundary: `agentmarshal validate` and the project's tests work
cleanly as required checks in CI (they read the committed tree). The
review-bound gate lane, however, needs the review evidence present in the
CI checkout, which on GitHub means materialising it from the PR's
approval — a provider-integration step deferred to Phase C (and connected
to the record-provenance trust boundary). So this slice runs the gate as
an advisory (non-blocking) check now, documented to become required once
review materialisation lands; the journal-only lanes (openings,
completions) and the scope/append-only/base-state/lifecycle checks it
already enforces are exercised immediately.

## Objective

Ship a GitHub Actions workflow template and a setup doc for Variant-2
governance: `validate` + tests as required checks now, the gate as an
advisory check with a documented path to required.

## Acceptance Criteria

- [ ] `templates/github/agentmarshal-governance.yml` is a valid GitHub
      Actions workflow: on pull requests (and pushes to the default
      branch) it checks out with full history, installs AgentMarshal, and
      runs `agentmarshal validate` and a project-tests placeholder as
      normal (required-suitable) steps; and runs
      `agentmarshal gate --attestation ci-required` deriving task from the
      head branch and passing head/base from the PR context, as an
      advisory step (`continue-on-error: true`) with an inline comment
      explaining the review-materialisation prerequisite.
- [ ] `docs/github-enforcement.md` documents the Variant-2 model: which
      checks to mark required in branch protection (`validate` + tests),
      why the gate is advisory until review materialisation, the link to
      the record-provenance trust boundary, and the contrast with the
      GitFlic Variant-1 invoked model.
- [ ] Placeholders (install source, project test command) are clearly
      marked for the adopter to fill; no secrets or private hosts/paths.
- [ ] The workflow YAML parses (valid syntax) and the doc is public-safe.
- [ ] `uv run agentmarshal validate` and the CI checks stay green.

## Non-Goals

- No GitHub review-API integration / review materialisation (Phase C).
- No actual migration of AgentMarshal to GitHub, no branch-protection
  configuration, no provider adapter code. No change to the gate, the
  CLI, or `am-merge`. Template and documentation only.

