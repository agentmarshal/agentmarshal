+++
schema = 1
id = "CR-142"
title = "Published text follows the step decision, the map covers ADR-0016..0021, and carried review advisories are closed"
scope = [
  "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
  "docs/adr/ADR-0014-where-things-live.md",
  "docs/adr/ADR-0016-the-lifecycle-of-review-findings.md",
  "docs/adr/ADR-0018-governing-the-contract.md",
  "docs/adr/ADR-0019-accounting-time-quota-resets-money.md",
  "docs/adr/ADR-0020-the-outbox-command-group.md",
  "docs/adr/ADR-0021-an-acknowledged-leak-scan-hit.md",
  "docs/proposals/041-the-next-step-of-a-task-is-decided-outside-the-tool.md",
  "docs/proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md",
  "docs/proposals/043-review-before-integration-makes-every-merge-stale.md",
  "docs/proposals/README.md",
  "docs/README.md",
]
acceptance = [
  "ADR-0014 decision 9, proposal 042 and its row in the proposals index carry a dated amendment (2026-10-03, the earlier text kept visible) saying the operator decided against a `step` stage the core feeds: the core records step events — a step started, with its kind of work, process, process start time and deadline, and a step ended with its outcome — in the process log, and status and doctor show a step past its deadline; the watchdog and the loop monitor are a supplied component the harness runs, and the core starts no background process; the step commands and the event fields are defined by the record model, a later decision without a number; nothing else in decision 9 changes",
  "the documentation map in docs/README.md has one line each for ADR-0016, ADR-0017, ADR-0018, ADR-0019, ADR-0020 and ADR-0021, in the style of the existing ADR lines, each saying what a reader learns there",
  "every item in the list under 'Advisories to close' in the body is closed in the named file — a wording slip corrected in place and listed in a short dated 'Corrections' note at the end of that document, anything that changes what a decision says made as a dated amendment — and each corrected statement matches the file it rests on",
  "no decision point is added or removed anywhere; proposals are referred to as 'proposal NNN' and linked; nothing names a private document, an adopter, a client, an unpublished release or an unpublished decision by number",
  "the full CI sequence passes",
]
+++

# CR-142: documentation tail after ADR-0016..0021

## Context

The operator decided against a `step` stage that the core would feed (the
core would have had to start and leave running processes and give a
personal extension the power to stop an implementer); ADR-0014 decision 9
and proposal 042 still describe it. Six ADRs were published without map
lines. Reviews of the published ADRs left advisories that are wording or
factual slips.

## Objective

The published text says what was decided, and the map leads to it.

## Advisories to close

1. ADR-0013, the amended state paragraph of decision 10: the Windows
   user-scope directories are attributed to the scope table, but the table
   names only the configuration directory; the data directory is on
   ADR-0014's map. Say where each is named.
2. ADR-0013, the manifest example names the adapter's lock
   `lock/adapter-lock.json`, while the dependency decision installs Python dependencies
   with `uv sync --locked`, which reads a `uv.lock`; make the example's file
   name one that command reads, and keep the text and the example in
   agreement.
3. ADR-0016: proposal 039's fifth ask (checking the whole set rather than a
   sample, accepted as documentation) is not answered — say where it is
   answered or that it is answered by documentation; "the findings lane is
   not affected" must say which effect it excludes.
4. ADR-0018 Context: the contract review is compared with the day's six
   candidate-review cycles in time as well as cost; proposal 033 compares
   cost only — the sentence must claim only what 033 measured.
5. ADR-0019: the fourth Consequences bullet must say the shared vocabulary
   makes a refusal, a crash and a truncation read differently from one
   another and the same way in every project; decision 8 must say the other
   half of proposal 032's third ask (exposing the journal-only lane to the
   required check) goes to the journal-transactions work of proposals 019
   and 035, as 032's disposition says.
6. ADR-0020: the list introduced as two proposals' measurements has three
   items; the outbox is not the only directory under `.agentmarshal/` that
   does not record the adopter's own work — `.agentmarshal/extensions/`
   (ADR-0014's map) is another.
7. Proposal 041: the report-ready flag is not "the same fact proposal 036's
   refusal rests on" — 036 rests on the session's commit and an outcome other
   than implemented; correct the disposition note.
8. Proposal 043: the Finding (the reporter's text, which stays) calls
   "gate → complete → merge" the recommended loop, while
   docs/self-hosting-workflow.md numbers merge before complete; add a short
   note after the Finding saying what the published workflow says about the
   order, and that the stale-merge observation holds either way.

9. ADR-0021, "What this revises": decision 3 (an acknowledged hit no longer
   makes the command exit 1) also revises the leak-scan spec's sentence that
   the command's exit status answers whether a hit was found; name it beside
   the two revisions already listed.

## Acceptance Criteria

As in the header.

## Non-Goals

- The record model and the step commands' fields (a later decision).
- Any other advisory, and any change to code.
