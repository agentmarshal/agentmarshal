## Why

[ADR-0011](../../../docs/adr/ADR-0011-contract-amendment-visibility.md) decided
that the party asked for an independent judgement should be told that the
document it judges against has a history. The decision is landed; nothing
implements it.

An adopter measured the gap on their own journal: six amendments across four
tasks, five recorded after implementation began, none visible to the reviewer at
verdict time. This repository carries more.

## What Changes

- The review prompt and the implementer's brief render the task's amendment
  records: when, why, and who recorded it when the record names an actor.
- A review record may carry `reviewed_contract`, the sha256 of the contract text
  the reviewer was handed, under a new record schema.
- A task with no amendment records produces the prompt and the brief it produces
  today, byte for byte.

## Impact

- `src/agentmarshal/journal/review.py`: the prompt gains a block; the launcher
  hashes the contract it read and passes it to the recorder.
- `src/agentmarshal/journal/brief.py`: the brief gains the same block.
- `src/agentmarshal/journal/records.py`: schema 5 and the field's validation.
- `src/agentmarshal/journal/submit_review.py`: passes the field through when it
  is given one; the human path never has one.
- No gate change, in any placement or lane. ADR-0011 D3.
