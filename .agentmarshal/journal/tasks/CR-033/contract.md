+++
schema = 1
id = "CR-033"
title = "migrate-journal --lenient: tolerate pre-v1 header deltas with a report"
scope = ["src/agentmarshal/migrate.py", "src/agentmarshal/cli.py", "tests/test_migrate.py"]
acceptance = []
+++

# CR-033: migrate-journal --lenient

## Context

The v1->v2 `migrate-journal` is strict: a task or review missing any
required header aborts the whole migration. Pre-v1 journals (a real adopter
case) carry small header deltas — a task without `Scope`, early reviews
without a reviewer identity or `Finding-IDs`. Strict mode cannot onboard
them without hand-editing history (which fabricates data). This adds an
opt-in lenient mode that migrates what is faithfully migratable and
transparently reports what it defaulted or skipped, without inventing data.

## Objective

Add `migrate-journal --lenient`: default the safely-defaultable missing
fields, skip records that cannot be faithfully reconstructed, and emit a
report of every default and skip — so a pre-v1 adopter can migrate without
mutating the source archive and without fabricated provenance. Strict mode
(the default) is unchanged.

## Acceptance Criteria

- [ ] `migrate-journal` gains a `--lenient` flag (default off). Strict
      behavior is byte-for-byte unchanged when the flag is absent.
- [ ] In lenient mode, a **task** missing `Scope` migrates with an empty
      scope (reported); a task missing/!invalid `Status` is skipped
      (reported), since its lifecycle cannot be projected. Missing
      non-essential headers (Owner/Type/Created) do not block.
- [ ] In lenient mode, a **review** is skipped (reported, not fabricated)
      when it lacks reviewer identity (Reviewer-Role/Vendor/Model/Email) or
      `Reviewed-Commit`, or when it is non-`approved` yet has no
      `Finding-IDs` to reconstruct, or when Verdict/Finding-IDs are
      inconsistent, or when its `Task` is not a valid task id. A review
      missing only `Finding-IDs` with an `approved` verdict migrates with
      no findings (reported).
- [ ] The migration emits a **report** listing every default applied and
      every skip with its reason; skipped reviews are simply absent from
      the migrated journal (never fabricated). The CLI prints the report.
- [ ] The migrated journal still validates (`load_task_status` projections
      hold) and the source archive is never modified.
- [ ] Tests cover: strict unchanged (missing header still aborts); lenient
      defaults empty scope; lenient skips a review missing reviewer
      identity; lenient skips a non-approved review missing Finding-IDs;
      lenient migrates an approved review missing Finding-IDs; the report
      names defaults and skips.
- [ ] `uv run agentmarshal validate`, pytest, ruff, format, and mypy stay green.

## Non-Goals

- No change to strict-mode behavior or output.
- No fabrication of missing data (no invented scope values, reviewer
  identities, findings) — lenient only defaults the semantically-safe and
  skips the rest with a report.
- No car-rental-specific logic — generic pre-v1 tolerance.
