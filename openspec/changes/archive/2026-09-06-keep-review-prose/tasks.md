## 1. Writing artifacts

- [x] 1.1 Add one helper that writes bytes to `tasks/<id>/artifacts/<name>` exclusively and returns `{ref, hash}` — verify: unit test writes, refuses to overwrite, returns a hash matching sha256 of the file.
- [x] 1.2 `agentmarshal review` writes the reviewer's output through the helper before writing the record and pins it — verify: launcher test finds the file named by the record id and the record's `artifacts` pin matches.
- [x] 1.3 `agentmarshal submit-review --prose FILE` copies the file through the helper and pins it; without the flag the record has no `artifacts` — verify: two CLI tests.

## 2. Holding artifacts to the record rule

- [x] 2.1 The gate's append-only check covers `tasks/<id>/artifacts/` paths — verify: gate test modifies a pinned artifact in a candidate and sees the refusal line.
- [x] 2.2 `validate` checks each review record's pinned artifacts exist and match their hash — verify: test corrupts an artifact and `validate` refuses naming the record.

## 3. Showing it

- [x] 3.1 `status` and `report` show `artifacts=N` on a review line that carries any — verify: existing status test extended.

## 4. Unchanged where unused

- [x] 4.1 The 0.3.0 byte-for-byte gate transcript test and the existing review-launcher tests pass unmodified — verify: `uv run pytest -q`.
- [x] 4.2 Docs: quickstart's review step and overview's Record entry mention the artifact in one sentence each — verify: read.
