+++
schema = 1
id = "CR-060"
title = "The economics report says how the counts it sums were obtained"
scope = ["src/agentmarshal/journal/report.py", "tests/test_report.py", "docs/quickstart.md"]
acceptance = [
  "a task line reports how its session counts were obtained, distinguishing counts a provider reported from counts measured afterwards",
  "a task whose sessions carry no usage provenance reports that too, rather than omitting the column",
  "a task mixing both kinds of session says so rather than picking one",
  "the summary line carries the same distinction across the whole journal",
  "a task with no session records at all keeps its current line, with tokens=0",
  "existing report lines keep their leading fields and tab separation, so a caller splitting on tabs still finds task, state, reviews and tokens where they were",
  "the quickstart shows recording a session and reading the report as part of the loop, not only as a closing suggestion",
]
+++

# CR-060: The economics report says how the counts it sums were obtained

## Context

Adopter proposal 008. CR-058 gave a session record an optional `usage` object
saying which provider the counts concern and whether the provider **reported**
them or they were **measured** afterwards from logs. Adopter B does the latter
and calls it lossy and unverifiable later.

That distinction currently stops at the record. `agentmarshal report` sums
`tokens` across sessions and prints one number, so a total assembled from
provider-reported figures is indistinguishable from one reconstructed by hand.
The report is where anyone actually looks at the economics, and the economics
claim is one of this project's stated purposes — a number whose origin is
invisible at the point of reading is the same problem CR-058 set out to fix, one
step further along.

Adopter C separately asks for token accounting to appear in the quickstart, so
an adopter meets it at the start rather than discovering it after months. Today
`record-session` and `report` appear only in the closing "what next" list.

## Objective

Carry the provenance distinction through to the report, and show accounting in
the documented loop.

## Acceptance Criteria

- A task line says how its session counts were obtained: counts a provider
  reported, counts measured afterwards, or that no provenance was recorded.
- A task whose sessions carry no `usage` says so; the information is not simply
  omitted.
- A task mixing sessions of different kinds says that, rather than reporting one
  of them.
- The summary line carries the same distinction for the journal as a whole.
- A task with no session records keeps the line it has today, with `tokens=0`.
- Existing fields keep their order and tab separation: a caller splitting a task
  line on tabs still finds task id, state, `reviews=` and `tokens=` where they
  are now.
- The quickstart shows recording a session and reading the report as a step of
  the loop, not only in the closing suggestions.

## Non-Goals

- Changing what a session record may contain. CR-058 settled that shape.
- Aggregating by provider name, or summing per provider.
- Changing `review_cycles`, the token arithmetic, or which records are counted.
- A machine-readable output format for the report. This task changes what the
  existing text says, not how it is encoded.
- Documenting anything beyond the accounting step in the quickstart.
