## 1. One listing

- [x] 1.1 `run_gate` derives `changed` from the decomposed listing and `_changed_paths` is deleted — verify: `grep -n "name-only" src/agentmarshal/journal/gate.py` finds only the base-tree `ls-tree`.
- [x] 1.2 Tests, one per scenario, named in the docstring: rename out of scope refused with the source named; rename within scope passes; move into the journal takes the diff lane — verify: each test fails when `changed` is taken from `git diff --name-only` again.
- [x] 1.3 The 0.3.0 byte-for-byte transcript test and the sidecar transcript tests pass unmodified — verify: `uv run pytest -q`.

## 2. Spec

- [x] 2.1 The new capability spec `scope-enforcement` is created by archiving this change (the lead archives) — verify: `openspec validate --all`.
