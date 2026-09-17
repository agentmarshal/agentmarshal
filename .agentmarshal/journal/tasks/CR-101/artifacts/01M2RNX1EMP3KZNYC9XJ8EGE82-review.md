I reviewed the diff against the contract, the named decisions (ADR-0009, ADR-0006), the change's `design.md`/`specs/`, and the surrounding code. Summary of what I verified:

**Correct and complete**
- Every scenario in `openspec/changes/archive/2026-09-18-review-binds-to-a-finding/specs/` (13 in `findings-review`, 2 in `reviewer-adapter`) has a test whose docstring names it.
- The commit prompt's rendered bytes are preserved: `_prose_instruction()` and `_verdict_protocol("reviewed_commit", …)` reproduce the 0.3.0 text character-for-character, and `_named_contract_material` with an empty `preamble` reproduces the old inline block exactly.
- The gate's findings transcript is byte-stable: `finding_reviewer_identity_refusal(..., launching=False)` returns the same two strings the inlined code produced, in the same order, for the same conditions.
- `artifact_path` exists once, in `artifacts.py`; `gate.py` and `review.py` both re-export the same function object, and `_artifact_path` is gone from `gate.py` (`src/agentmarshal/journal/gate.py:23`, `review.py:18`).
- All five pre-run refusals (not-latest, closed, scoped, dependent reviewer, drift/nothing-verifiable) run before `_run_reviewer` is reached (`review.py:836-858`).
- `create_review_record` stamps schema 5 for `reviewed_finding` + `reviewed_contract`; `_validate_record` allows that combination, so the post-reviewer write cannot fail on schema grounds.
- `ExtensionManifestMissing` subclasses `ExtensionManifestError`, so the new two-handler order in `review.py:874-880` is right.
- CLI: `--dry-run` still refuses `--reviewed-finding` through the pre-existing `ignored` list; `--base` is refused beside a finding; `require_host` is correctly relaxed only for the finding path.
- No scope violation — every changed path is covered by the contract's `scope`.

Two advisory points, neither blocking:

`verdict-both-subjects-refusal-misleads` — In `src/agentmarshal/journal/review.py:580-587`, when a finding review's reviewer prints *both* `reviewed_commit` and `reviewed_finding`, `len(bindings) == 2` and the refusal reads "reviewer verdict must name reviewed_finding" — which the reviewer did do. The mirror case on the commit path gives the actionable "reviewer verdict has unsupported field(s): reviewed_finding". A reviewer handed the finding-path message has no way to learn that the extra key is the problem.

`artifact-prefix-comment-overclaims` — In `src/agentmarshal/journal/review.py:46-50`, the comment on `_ARTIFACT_CONTENT_PREFIX` ends "An empty line takes the bar alone, so the prompt never carries trailing whitespace." The mechanism only covers empty lines; a pinned artifact line that itself ends in a space still puts trailing whitespace in the rendered prompt. The absolute claim is broader than what the code does — the same overreach this project's prior reviews have flagged in its own prose.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "3a95a761f7825cecd7a115ef0fb0f14b0e9f43ba", "verdict": "approved", "findings": [], "advisory_findings": ["verdict-both-subjects-refusal-misleads", "artifact-prefix-comment-overclaims"]}
AGENTMARSHAL_VERDICT_END
