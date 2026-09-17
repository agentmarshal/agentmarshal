## 1. The rendering

- [x] 1.1 The review prompt carries an amendment block after the contract when the task has amendment records — verify: launcher test naming the scenario, asserting time and reason of each record.
- [x] 1.2 The brief carries the same block with the same wording — verify: brief test naming the scenario.
- [x] 1.3 An amendment record without a recorder renders without naming one — verify: test with a record carrying no `recorded_by`.
- [x] 1.4 A task with no amendment records produces the prompt and brief unchanged — verify: the pinned 0.3.0 prompt test and the brief tests pass unmodified.
- [x] 1.5 The records are read from the journal the command works in, so an amendment recorded after the reviewed commit appears — verify: test that records an amendment after building the candidate.

## 2. The record field

- [x] 2.1 Schema 5 allows `reviewed_contract`; a writer stamps 5 only when the field is present — verify: records test on both branches.
- [x] 2.2 A record carrying the field under an earlier schema is refused, and the message names the field — verify: records test on the message.
- [x] 2.3 `agentmarshal review` records the sha256 of the contract bytes the prompt carried — verify: launcher test comparing the record's field with the hash of the contract in the prompt.
- [x] 2.4 `submit-review` records no field and stays valid — verify: journal test.
- [x] 2.5 Existing records are read unchanged — verify: `uv run agentmarshal validate` over this journal, plus the byte-for-byte gate transcript test.

## 3. Nothing else moves

- [x] 3.1 No gate line is added in any placement or lane — verify: the gate transcript tests, embedded and sidecar, pass unmodified.
