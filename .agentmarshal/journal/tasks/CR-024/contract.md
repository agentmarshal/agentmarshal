+++
schema = 1
id = "CR-024"
title = "GitHub and PyPI readiness artifacts"
scope = [".github/workflows/agentmarshal-governance.yml", ".github/workflows/release.yml", "pyproject.toml"]
acceptance = []
+++

# CR-024: GitHub and PyPI readiness artifacts

## Context

Phase 0 of the GitHub migration + PyPI setup
(`research/v2/runbooks/2026-07-28-github-migration-pypi.md`): prepare the
in-repo artifacts so the operator can move AgentMarshal to a private
GitHub repo and wire PyPI publishing. pip-installability is already
verified (a bare `pip install` builds the wheel via the uv_build PEP517
backend and the console script runs). This slice adds AgentMarshal's own
GitHub Actions governance workflow, a tag-triggered PyPI release workflow
using Trusted Publishing (OIDC), and PyPI-facing packaging metadata.

The files are inert until the move: GitFlic ignores `.github/`, and the
release workflow only fires on a `v*` tag once the PyPI publisher is
configured.

## Objective

Ship the GitHub Actions governance and release workflows and the
packaging metadata needed for the private-GitHub move and PyPI publishing.

## Acceptance Criteria

- [ ] `.github/workflows/agentmarshal-governance.yml`: on pull requests
      and pushes to the default branch, checks out with full history,
      sets up uv, and runs `agentmarshal validate`, pytest, ruff check,
      ruff format --check and mypy as normal (required-suitable) steps;
      plus an advisory (`continue-on-error`) `gate` job running
      `agentmarshal gate --attestation ci-required` deriving task from the
      head branch and head/base from the PR context. Least-privilege
      `permissions: contents: read`.
- [ ] `.github/workflows/release.yml`: on a `v*` tag, builds the sdist and
      wheel and publishes to PyPI via `pypa/gh-action-pypi-publish` with
      OIDC (`id-token: write`, environment `pypi`) — no API token. A
      comment records the pending-publisher settings the operator must
      configure on PyPI.
- [ ] `pyproject.toml` gains PyPI-facing metadata: `keywords` and
      `classifiers` (no license classifier — the SPDX `license` field is
      authoritative). No repository URL is hardcoded (added post-move when
      the GitHub URL exists); no personal email is added.
- [ ] Both workflows are valid GitHub Actions YAML; no secrets, no private
      hosts or paths; the release workflow is inert without a tag and a
      configured publisher.
- [ ] `uv run agentmarshal validate` and the CI checks stay green.

## Non-Goals

- No actual GitHub repository, push, branch protection, or PyPI account /
  publisher configuration (operator, Phases 1 and 3). No gh-based invoked
  merge and no review materialisation (later slices). No change to the
  gate, CLI, `am-merge`, or the adopter template `templates/github/…`.

