## 1. The level

- [ ] 1.1 Both review paths resolve the `reviews` level through `capture_policy_from_project` from the project file of the journal being written — verify: grep finds no second reading of the setting.
- [ ] 1.2 `agentmarshal review` resolves the level before launching the reviewer — verify: test with a malformed section and a reviewer command that records it was run.

## 2. The behaviours

- [ ] 2.1 `commit`: artifact written and pinned, stderr line unchanged — verify: test.
- [ ] 2.2 No capture section (`hash`): no artifact, no `artifacts` on the record, output in a named local temporary file — verify: test.
- [ ] 2.3 `off`: no artifact, no temporary copy, stderr says so — verify: test.
- [ ] 2.4 `submit-review --prose` under `hash` and `off` refused before writing — verify: test that the artifacts directory and records are unchanged.
- [ ] 2.5 A rejected verdict's output is kept as before at every level — verify: test at `off`.

## 3. The repository and the documents

- [ ] 3.1 `.agentmarshal/project.json` sets `capture.overrides.reviews` to `commit` — verify: `agentmarshal validate` and `doctor` still pass.
- [ ] 3.2 Existing tests that expect pinned prose set `commit` in their project fixture rather than lose their assertion — verify: full test suite.
- [ ] 3.3 README.md, UPGRADING.md, CHANGELOG.md (0.4.0), docs/quickstart.md, docs/overview.md and ADR-0005's status note state the default and the setting — verify: grep for "No setting turns this off" finds nothing.
