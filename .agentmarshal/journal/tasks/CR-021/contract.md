+++
schema = 1
id = "CR-021"
title = "Document the self-hosted v2 workflow"
scope = ["docs/self-hosting-workflow.md"]
acceptance = []
+++

# CR-021: Document the self-hosted v2 workflow

## Context

After the self-hosting flip (2026-07-27) the repository governs itself on
v2, but the working flow lives only in session memory and retros. New
contributors and future sessions need a single reference: how a task
travels open -> implement -> review -> merge -> complete on v2, which
commands are authoritative, and which v1 pieces are superseded versus
still used as infrastructure (the v1 provider merge API and the review
launcher are reused by `am-merge`/review; `merge-policy.sh`,
`task-lifecycle.sh` and the agmake managed cycle are superseded).

## Objective

A concise `docs/self-hosting-workflow.md` documenting the v2 governance
workflow and the live-vs-superseded boundary of the v1 tooling.

## Acceptance Criteria

- [ ] `docs/self-hosting-workflow.md` describes the full v2 lifecycle:
      `agentmarshal open` (contract committed via a journal-only opening
      merged with `am-merge`), implement on a branch, independent review
      recorded with `agentmarshal submit-review`, merge via `am-merge`
      (v2 gate as authority, provider merge reused), and `agentmarshal
      complete` plus its completion-record merge.
- [ ] It states the authority model: `am-merge` runs `agentmarshal gate`
      and, on pass, reuses the v1 provider merge API with the v1
      merge-policy skipped; `gate`/`validate` are the v2 checks.
- [ ] It lists the live-vs-superseded boundary: still used — the v1
      provider `mr.sh get`/`merge` and the review launcher; superseded —
      `merge-policy.sh`, `task-lifecycle.sh`, the agmake managed cycle.
- [ ] Public-safe: no private hosts, tokens, or internal-only paths.
- [ ] `uv run agentmarshal validate` and the CI checks stay green.

## Non-Goals

- No code changes; documentation only. No removal of the v1 submodule
  (its provider adapter and review launcher are still used). No new
  tooling.

