I read the full diff against the snapshot, traced the record-validation ladder, the two rendering paths, and every scenario-to-test mapping the contract requires. Summary of what I verified:

- **Scenario coverage (AC1):** all nine scenarios across `specs/contract-history/spec.md` and `specs/review-evidence/spec.md` are named verbatim in a test docstring. The implementation matches design.md's six decisions — one constant, no block when there are no amendment records, write order via ULID-sorted filenames (`records.py:1043` + `_record_path`), hash over the bytes read, schema-5 shape, pass-through in `submit_review`.
- **Byte-for-byte (AC2):** `append_amendment_history` returns its input unchanged when the history is empty, so the pinned 0.3.0 prompt and the existing brief output are untouched; the pinned test's expectations are unmodified (only its docstring gained a line).
- **Read side (AC3):** `launch_review` renders from `load_task_status(journal_root, …)` — the active journal in both placements — while `contract_path` still branches to the sidecar tree or the reviewed commit's snapshot. Correct, and this very prompt demonstrates it.
- **Schema 5 (AC4):** the `reviewed_contract`-before-unexpected-fields ordering in `_validate_record` (`records.py:227-228`) is what makes the refusal name the field rather than degrade to "unsupported fields"; `_SHA256_HEX_PATTERN.fullmatch` still rejects a trailing newline. The writer floor stays 3/4. Nothing existing can become invalid, since only an accepted schema and an accepted field were added.
- **Nothing else moved (AC5):** no hunk touches `gate.py` or `gate_context.py`; every changed path is inside the declared scope; `tasks.md` is fully ticked.
- **Injection surface:** reasons are `> `-quoted per line and the actor name is whitespace-collapsed, so neither can forge an entry or a heading. The docstring's claim holds.

Two advisory points, neither blocking:

**ADV-CR096-001** — `docs/adr/ADR-0004-journal-data-model.md:143-151` enumerates the schema ladder through schema 4 ("Schema 4 adds findings and finding-bound review, acceptance and completion records… Loaders continue to accept schemas 1 and 2 unchanged"). Schema 5 now exists and that paragraph reads as a complete history. When schema 4 landed, ADR-0009's "Other documents this reaches" explicitly made extending that sentence the implementation task's job; ADR-0011 carries no equivalent instruction and `docs/adr/` is outside CR-096's scope, so this could not be fixed here — it needs booking as follow-up rather than repair in this diff.

**ADV-CR096-002** — `render_amendment_history` and `append_amendment_history` are defined in `src/agentmarshal/journal/brief.py:19-52` and imported by `src/agentmarshal/journal/review.py:16-19`. The renderer is a record-derived concern belonging to neither party's briefing, and the placement makes the reviewer prompt depend on the implementer-briefing module, whereas design.md's Context treats `review.py` and `brief.py` as peers. A neutral home would avoid that one-way coupling. Behaviour is correct either way; there is no import cycle.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "9d2cea0a68727f05d67c88e921c7d09852e59ee2", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-CR096-001", "ADV-CR096-002"]}
AGENTMARSHAL_VERDICT_END
