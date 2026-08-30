# 005 — Research findings have no record type

- **Reporter:** Adopter A · **Observed on:** 0.1.0 · **Disposition:** deferred

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

The gap is real and we have felt it too. Deferring on sequencing, not merit:
this interacts with the record schema and with the in-toto projection that is
already specified but not built, and adding a record type before that projection
exists risks designing a field twice.

Worth noting what the report is careful not to ask for: it does not propose that
AgentMarshal store research content itself, only that a task's findings have
somewhere to be recorded.
