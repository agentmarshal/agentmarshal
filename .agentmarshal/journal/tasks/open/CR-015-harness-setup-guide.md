# CR-015: harness setup guide and permission templates

Owner: lead
Type: docs
Priority: P2
Created: 2026-07-19
Status: in_review
Scope:
- .agentmarshal/journal/tasks/open/CR-015-harness-setup-guide.md
- docs/
- docs/templates/

## Context

Onboarding (founding brief §4.2-5) must not strand a new adopter on
harness permission friction. Our own dogfooding produced the source
material: every autonomous run this session stopped at least once on a
harness permission prompt, never on the rails themselves. This slice
captures the best-practice setup as a public-safe guide plus copyable
permission templates for the harnesses we use — Claude Code and Codex
CLI — so an adopter reaches a friction-free flow on day one.

Design constraints (binding):

- **Public-safe by construction:** the guide and templates contain no
  private paths, usernames, hostnames, tokens or references to
  non-public repositories. Paths are placeholders
  (`<your-repo>`, `~/…`) and permission rules are generic.
- Documentation and JSON/text templates only; no code, no changes to
  the package.

## Objective

`docs/harness-setup.md` explains how to configure a harness to run the
AgentMarshal rails without permission friction, and `docs/templates/`
holds copyable starting-point permission templates.

## Acceptance Criteria

- [ ] `docs/harness-setup.md` exists and, public-safe, covers: why
      permission setup matters (agents stall on prompts, not on the
      rails); the allowlist approach for Claude Code
      (`.claude/settings.local.json`); the reason command substitution
      `$(...)` cannot be allowlisted and the wrapper-script pattern that
      avoids it; adding working temp directories to
      `additionalDirectories`; and the equivalent Codex CLI setup
      (trusted project, model selection).
- [ ] `docs/templates/claude-code-settings.local.json` is a valid JSON
      starting-point allowlist covering the rail command families (git
      verbs, the package check commands, the framework scripts via a
      placeholder path) with an inline note that it is a starting point
      to adapt.
- [ ] Nothing in the guide or templates contains a real username, home
      path, hostname, token, or private repository name; a reviewer can
      confirm public-safety by inspection.
- [ ] The templates are internally consistent with the guide (the guide
      references them accurately).
- [ ] No package code changes; `uv run pytest`, `ruff check`,
      `ruff format --check`, `mypy` still pass unchanged in CI.

## Non-Goals

- No `init`-time automatic generation of these templates (wiring the
  guide into `init` is a later slice), no harness adapters/skills, no
  Codex TOML generation.
- Do not modify the `agentmarshal/` submodule, `gitflic-ci.yaml`, or
  anything under `.agentmarshal/` beyond this contract file.
