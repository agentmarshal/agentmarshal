+++
schema = 2
id = "CR-172"
title = "docs/threat-model.md states what the tool protects against and what it does not, from the published decisions"
scope = ["docs/threat-model.md", "docs/README.md", "SECURITY.md"]
acceptance = [
  "docs/threat-model.md exists, in English, and states only what published material already decides: every statement cites its source — an ADR by number and decision or section, a spec under openspec/specs/ by capability and requirement header, README.md or SECURITY.md — never by line number; it says that it decides nothing itself and that its sources win where they differ; a source that is decided but not implemented, or on the roadmap, is marked so; no statement is stronger than its source (no absolute where the source qualifies)",
  "the document has three parts: what the tool protects (among them the contract, manifests, markers and lifecycle read from the base side; append-only records; the verdict bound to the commit; acceptance that is not a bypass; escaping of forgeable text; leak-scan output that does not print what it withholds; the symlink refusals the specs state; the host never written in a sidecar; extensions that cannot change the gate's decision; a gate that reads nothing local); what it does not protect against (among them declared, unauthenticated identity; the trusted checkout, reviewed tree and pipeline; local state and the process log against processes of the same OS user; a best-effort leak scan; no signing and no SLSA level; records written around the tool and the journal-only lane; the sidecar's limits; extension and executor isolation outside the core); and the questions the published material leaves open, each stated as open with its sources and not resolved",
  "a section says how to classify a finding: a security defect breaks a promise of the first part — in agreement with SECURITY.md's list; a weakness the second or third part covers is a hardening suggestion, not a vulnerability; SECURITY.md gains one sentence pointing to docs/threat-model.md and no other change of meaning",
  "docs/README.md's map gains one line for docs/threat-model.md and the line it lacks for ADR-0023 (docs/adr/ADR-0023-next-the-next-step-of-a-task.md), in the form of the lines around them, and nothing else changes in it",
  "the full CI sequence passes",
]
+++

# CR-172: the project's threat model in one document

## Context

The published decisions already say what AgentMarshal protects and what it
does not — ADR-0006 (identity declared, not proven), ADR-0004 and ADR-0017
(the trusted checkout), ADR-0014 decision 8 and ADR-0013 decision 15 (local
state against processes of the same user), ADR-0005 (a best-effort leak
scan), SECURITY.md's list of what counts as a vulnerability — but scattered
over twenty-three ADRs and the specs. Reviewers and finders cannot see the
boundary in one place, so a weakness the decisions knowingly leave open is
raised as a blocking defect again and again. Operator decision 2026-10-04:
collect the boundary into docs/threat-model.md, from published material only.

## Objective

One document a reviewer, an implementer or a finder reads to tell a security
defect from a hardening suggestion.

## Acceptance Criteria

As in the header.

## Non-Goals

- Deciding anything new, or resolving an open question: the document collects
  and cites, and names what is open as open.
- Changing any ADR, spec, code, test or other document (docs/overview.md's
  wording and docs/known-defects.md included).
- Protection beyond what the published decisions promise, including against
  processes of the same OS user.
