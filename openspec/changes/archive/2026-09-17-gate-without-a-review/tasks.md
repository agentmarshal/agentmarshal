## 1. The mode

- [x] 1.1 `gate` accepts the request and, with no review record for the candidate, reports both review-bound checks as not examined with the reason, without refusing — verify: gate test naming the scenario.
- [x] 1.2 The mode does not excuse any other rule: a scope violation still refuses under it — verify: gate test naming the scenario.
- [x] 1.3 A non-approving review still refuses under the mode, and an approving one reports as usual — verify: two gate tests naming their scenarios.
- [x] 1.4 A run without the mode is byte-for-byte what it was: the pinned 0.3.0 transcript test and the sidecar transcript tests pass with their expectations unmodified — verify: `uv run pytest -q`.

## 2. The template and the document

- [x] 2.1 The shipped template asks for the mode and carries no guard of its own; `continue-on-error` is gone from that job — verify: read the template.
- [x] 2.2 `docs/github-enforcement.md` describes the arrangement that now exists, not the one it replaces — verify: read.
