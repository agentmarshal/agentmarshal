+++
schema = 1
id = "CR-035"
title = "migrate --lenient preserves approved-with-findings as advisory"
scope = ["src/agentmarshal/migrate.py", "tests/test_migrate.py"]
acceptance = []
+++

# CR-035: migrate --lenient preserves approved-with-findings as advisory

## Context

CR-033 made lenient migration *skip* a pre-v1 approved review that carried
findings, because the v2 model then required approved ⟺ no findings —
rewriting it would have altered the evidence. CR-034 added
`advisory_findings` (non-blocking findings on any verdict). Now the
faithful move is available: a pre-v1 "approved with findings" review can
migrate as `approved` with those findings recorded as **advisory** — no
loss, no misrepresentation (they were non-blocking follow-ups all along).
This recovers the completion-review attestations that CR-033 skipped.

## Objective

In lenient mode, migrate a pre-v1 approved review that carries findings by
reclassifying those findings as `advisory_findings` (keeping the approval),
reported — instead of skipping it. Every other inconsistency and skip is
unchanged.

## Acceptance Criteria

- [ ] In lenient mode, an approved review with findings migrates as an
      approved review whose `findings` are empty and whose
      `advisory_findings` are those original findings, and the
      reclassification is reported. The migrated record validates (approved
      + advisory findings is valid per CR-034).
- [ ] Every other lenient behavior is unchanged: a non-approved review with
      no findings is still skipped; a review missing reviewer identity or
      Reviewed-Commit is still skipped; strict mode still raises on any
      inconsistency.
- [ ] Tests: an approved-with-findings review migrates with the findings as
      advisory (reported); a non-approved-with-no-findings review is still
      skipped; strict mode still aborts on an approved-with-findings review.
- [ ] `uv run agentmarshal validate`, pytest, ruff, format, and mypy stay green.

## Non-Goals

- No change to strict mode or to any other lenient path.
- No change to the review model (CR-034) or the gate.
