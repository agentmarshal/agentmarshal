# 005 — Research findings have no record type

- **Reporter:** Adopter A (Python web service on Linux) · **Observed on:** 0.1.0 · **Disposition:** accepted *(2026-09-01; deferred at intake)*

**Implemented 2026-09-06:** [ADR-0009](../adr/ADR-0009-research-findings-lifecycle.md)
defines the findings lifecycle, implemented by CR-086.

## Finding

Some tasks produce knowledge rather than a diff: an audit, an investigation, a
technical assessment of an external system. The lifecycle has no record type for
the result. Adopter A reports a task whose entire output was four facts about an
external system; they were reported in chat, and a day later the project's own
register of open questions still showed them unanswered. Nothing in the journal
had a place to hold them.

The related observation is process rather than schema: a rule that never became
a step in the loop does not get executed.

## Proposed

A record type for findings produced by a task, so that research output lands in
the journal instead of chat.

## Disposition — deferred

> Superseded 2026-09-01: **accepted**. The deferral's reasoning below stands
> as history; the decision and what changed are in the dated section at the end.

The gap is real and we have felt it too. Deferring on sequencing, not merit:
this interacts with the record schema and with the in-toto projection that is
already specified but not built, and adding a record type before that projection
exists risks designing a field twice.

Worth noting what the report is careful not to ask for: it does not propose that
AgentMarshal store research content itself, only that a task's findings have
somewhere to be recorded.

## Disposition — accepted (re-read 2026-09-01)

The deferral was sequencing, and the sequence has arrived. The in-toto
Statement projection this waited on is scheduled in the current release plan,
so the record type can be shaped once, alongside it. And ADR-0008 answered the
question the original disposition left open — *where* research records belong:
a journal is now a thing that can live beside a repository rather than only
inside it, which is precisely the shape research evidence needs when the
research is private and the code is not.

External corroboration arrived independently: a published practitioner
workflow (PRD files in a personal directory, with attempt logs — the RA PID
write-up, 2026-08) demonstrates people building exactly this by hand.

Accepted with the sequencing that avoids designing the field twice: the shape
is decided during our own sidecar dogfood, together with the projection work.
What the report was careful not to ask for still holds — the tool records that
findings exist and where they are pinned; it does not become a store for
research content.
