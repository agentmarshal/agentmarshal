## 1. One copy of the prose

- [x] 1.1 `agentmarshal review` keeps no temp copy when the record pins the prose; the rejected-verdict path is untouched — verify: launcher test asserts no `agentmarshal-verdict-findings-*` file appears on an accepted verdict with findings, and the existing rejected-verdict test still passes.
- [x] 1.2 The CLI prints `reviewer prose pinned: <ref>` on success and no `kept at` line; `SubmittedReview.reviewer_output_path` is documented as the rejected path's field or removed — verify: CLI test on stderr.

## 2. No orphan a writer can foresee

- [x] 2.1 One function in `records.py` performs the pre-write refusals `write_record` applies (shape, finding binding, task, recorder identity); `write_record` and `submit_review` both call it — verify: the duplicated `reviewed_finding` message exists once; test that a binding to an unknown finding with `--prose` writes no artifact.
- [x] 2.2 When the record write fails after the artifact was written, the error names the artifact's path — verify: test that makes `write_record` fail (id collision) and checks the message.

## 3. Collisions

- [x] 3.1 The gate's base-tree collision check covers artifact paths — verify: gate test adds an artifact path present in the base tree and sees the refusal.

## 4. Spec and docs

- [x] 4.1 The baseline spec is updated by archiving this change (MODIFIED requirements) — verify: `openspec validate --all`.
- [x] 4.2 docs: the quickstart's review step no longer mentions a temporary file on success; overview unchanged — verify: read.
- [x] 4.3 The 0.3.0 byte-for-byte gate transcript test and the existing tests pass unmodified except the ones this change's scenarios replace (the CR-054 temp-copy tests) — verify: `uv run pytest -q`.
