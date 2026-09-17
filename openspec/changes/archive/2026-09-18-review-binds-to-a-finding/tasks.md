## 1. The launcher accepts a finding

- [x] 1.1 A review launched against a finding of the task records a review naming that finding and no commit, with the reviewer's prose pinned — verify: launcher test reading the written record.
- [x] 1.2 A verdict naming another finding, or naming a commit, is refused and nothing is recorded — verify: launcher test on both shapes, asserting the refusal names what was asked and what arrived.

## 2. The pinned bytes, and refusals

- [x] 2.1 Every reference that resolves under the project root is hashed before the reviewer runs, and a mismatch refuses the launch naming the artifact — verify: launcher test that edits a pinned file.
- [x] 2.2 A finding none of whose references resolve locally is refused — verify: launcher test.
- [x] 2.3 A reference that does not resolve locally is named in the prompt as unverified while the verified ones are included — verify: test on the built prompt.
- [x] 2.4 The resolver that decides "resolves locally" is one function, read by both the gate and the launcher — verify: the gate's own tests still pass with `_artifact_path` gone from `gate.py`.

## 3. The commit path is untouched

- [x] 3.1 The pinned commit-prompt test passes with its expectation unmodified — verify: run it; the expectation file is not in the diff.
- [x] 3.2 The CLI no longer refuses `review --reviewed-finding`, and `--dry-run` still refuses it — verify: CLI tests for both.
