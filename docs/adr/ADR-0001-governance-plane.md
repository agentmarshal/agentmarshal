# ADR-0001: Governance plane, not execution plane

Status: Accepted
Date: 2026-07-19

## Context

Agent harnesses (Claude Code, Codex CLI and their peers) natively provide
the execution plane for agent work: sandboxing, tool permissions,
worktree isolation, subagent orchestration, live session management.
These capabilities are vendor-maintained, improve rapidly and are free to
adopters.

What harnesses provide ends with the session. Transcripts are ephemeral,
vendor-bound and machine-local. A harness-side "review" is typically the
same agent or vendor reviewing itself, with no durable record bound to a
commit. Client-side hooks run under the control of the very executor
whose work needs checking. Nothing survives as portable evidence that a
given change was independently reviewed at a given commit — and with
growing autonomy this is a threat model, not a hypothetical: a
prompt-injected or hallucinating agent approving its own output.

AgentMarshal v1 (bash; archived read-only in the `agentmarshal/`
submodule) demonstrated both halves of this split in practice. Most of
its code implemented governance mechanics with no harness analogue:
merge policy, SHA-bound review records, task lifecycle, trusted
recorders, branch policy as protocol data. Its execution-side machinery
— worktree management, vendor launch glue — duplicated what harnesses
have since made native, and was the first code to become obsolete.

## Decision

AgentMarshal v2 is a governance plane and deliberately not an execution
plane.

We build durable, vendor-neutral, SHA-auditable evidence rails at the
integration boundary:

- task contracts (goal, acceptance criteria, scope) recorded in the
  repository before work starts;
- independent review bound to the exact reviewed commit, produced
  through a trusted recording path;
- merge gates that verify review, reviewer independence, pipeline
  attestation and scope conformance at the merge boundary;
- completion evidence and measurement, written by trusted recorders.

The repository — not a vendor UI or session log — is the system of
record.

We adapt to, and do not duplicate, the execution plane: sandboxing, tool
permissioning, isolation, live orchestration, session management belong
to harnesses. Harness-specific glue is confined to thin adapters.

Authority placement follows from the threat model: **gate authority
lives only server-side** (CI plus the merge boundary). Client-side
mechanisms — git hooks, harness hooks — are advisory fail-fast layers;
the executor controls them, so they are never trusted as enforcement.

## Consequences

- The product survives harness releases: new harness capabilities
  strengthen the execution plane we depend on instead of competing with
  what we build.
- Any executor — interactive agent, human, headless driver — rides the
  same rails, and switching vendors preserves both evidence and process.
- We inherit execution quality and isolation from harnesses; defects
  there are out of scope by design, and we do not attempt to compensate
  for them client-side.
- Enforcement is layered — advisory local hooks, trusted CI jobs,
  authoritative merge gate — and the layers must stay coherent: an
  advisory layer must never be the only thing standing between an
  unreviewed change and the target branch.
- Follow-up ADRs will fix the unit of isolation, the role of scope as a
  coordination overlay, and the journal data model.
