+++
schema = 1
id = "CR-025"
title = "Ship the py.typed marker"
scope = ["src/agentmarshal/py.typed", "pyproject.toml"]
acceptance = []
+++

# CR-025: Ship the py.typed marker

## Context

First task run entirely on the GitHub rails (dogfooding the new flow:
`agentmarshal open` -> PR -> governance check on GitHub Actions -> review
-> `gh-am-merge` -> `complete`). The package is fully type-annotated and
checked with mypy strict, but ships no `py.typed` marker, so downstream
type checkers ignore its types (PEP 561). Add the marker and re-declare
the `Typing :: Typed` classifier that was dropped for lacking it.

## Objective

Ship PEP 561 inline type information so downstream projects type-check
against AgentMarshal.

## Acceptance Criteria

- [ ] `src/agentmarshal/py.typed` exists (empty marker file) and is
      included in the built wheel (the uv build backend packages package
      data under `src/agentmarshal/` by default).
- [ ] `pyproject.toml` re-adds the `Typing :: Typed` classifier.
- [ ] `uv run agentmarshal validate`, `pytest`, `ruff check`,
      `ruff format --check`, `mypy` stay green locally and in CI.

## Non-Goals

- No code or type-annotation changes; no other packaging changes. Just
  the marker and the classifier.

