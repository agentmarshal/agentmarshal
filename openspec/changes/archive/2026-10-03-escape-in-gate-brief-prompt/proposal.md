## Why

ADR-0015 decision 5: rules that guard output apply by escaping on display.
CR-155 did it for `status` and `report` and left the gate's transcript, the
brief and the reviewer prompt as later work. They are this change. A record
the current rule cannot reach at read time — written under an earlier
schema, or written around the writer with a lowered schema — can still
carry a character that adds a line to what is printed or makes it read in
an order its bytes do not have: a newline in a finding id prints a line the
gate never said, including one that reads as an approval, and a
bidirectional override in a name the brief or the prompt renders reorders
what the reader sees.

## What Changes

Everything the gate's transcript, `agentmarshal brief` and the reviewer
prompt take from a record or a contract goes through
`escape_for_display` — the same function, consulting the same predicate the
writer refuses with. The record-text-safety requirement that named these
three renderers as later work now covers them, with a scenario for each.

## Capabilities

- modified: `record-text-safety`

## Impact

Nothing a record or a contract carries can forge a line or reorder text in
the gate's transcript, the brief or the reviewer prompt. A value the rule
accepts prints byte-identically, so records without such characters change
nothing — the pinned gate fixtures and the pinned prompts are untouched.
