## Why

ADR-0015 decision 5: rules that guard output apply by escaping on display. A
record the current rule cannot reach at read time — written under an earlier
schema, or written around the writer with a lowered schema — can still carry
a character that adds a line to what is printed or makes it read in an order
its bytes do not have, and `status` and `report` print those values as they
are. A newline in a record field would print a line the tool never said; a
direction-control character would reorder what is seen.

## What Changes

One function renders every character the forgeable-text rule refuses as a
visible escape — `\n`, `\r` and `\t` by name, `\uXXXX` (`\UXXXXXXXX` past the
Basic Multilingual Plane) for the rest — and everything `agentmarshal status`
(the task list and the per-task view) and `agentmarshal report` take from a
record or a contract goes through it. The record-text-safety specification
changes from refusal only to refusal at write and escaping on display.

## Capabilities

- modified: `record-text-safety`

## Impact

Nothing a record carries can forge a line or reorder text in `status` or
`report`; a value the rule accepts prints byte-identically, so records without
such characters change nothing. The gate's transcript, the brief and the
reviewer prompt are unchanged — a later task.
