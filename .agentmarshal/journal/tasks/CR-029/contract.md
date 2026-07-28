+++
schema = 1
id = "CR-029"
title = "capture policy config + mandatory leak-scan"
scope = ["src/agentmarshal/journal/capture.py", "tests/test_capture.py"]
acceptance = []
+++

# CR-029: capture policy config + mandatory leak-scan

## Context

ADR-0005 Decision 2 defines the capture policy that governs only the
supplementary layer (economics, review/prompt text, raw sessions): a
preset (`minimal` / `attested` (default) / `full`) with optional per-class
overrides, a mandatory leak-scan on every artifact before it is committed,
and the rule that raw sessions stay private by default at every preset —
public session commit is a separate escalation needing two independent
opt-ins. The always-on attestation records are out of scope of the policy
(CR-027), so `minimal` never drops the journal below in-toto Statement
completeness.

This slice builds the policy model, its resolver, the session-privacy
guard, and the leak-scanner as a tested library. Wiring it into forward
capture and the backfill are later CRs, so nothing here changes what is
written yet.

## Objective

Provide a deterministic capture-policy model resolvable from the project
config, and a mandatory best-effort leak-scanner, so later capture paths
can ask "what level applies to this class?" and "is this artifact safe to
store?" without re-implementing the rules.

## Acceptance Criteria

- [ ] `src/agentmarshal/journal/capture.py` defines the capture classes
      (economics, reviews, sessions), the levels (off / hash / commit),
      and the three presets with the ADR-0005 Decision 2 mapping:
      `minimal` = all off; `attested` = economics commit, reviews hash,
      sessions hash; `full` = economics commit, reviews commit, sessions
      hash (never public by preset).
- [ ] A `CapturePolicy` is parsed from a project-config object's optional
      `capture` section (preset + per-class overrides +
      `allow_public_sessions`), defaulting to `attested` when the section
      is absent, and failing closed on an unknown preset, class, level, or
      field.
- [ ] A resolver returns the effective level for a class (override beats
      preset). A session-privacy guard returns whether a session may be
      committed publicly, and it can only ever be true when BOTH
      `allow_public_sessions` is set in config AND a per-operation flag is
      passed — neither alone suffices; the preset/override path can never
      yield a public session.
- [ ] `scan_for_leaks(text)` returns the list of leak categories found
      (private key blocks, common tokens/keys, and any configured private
      markers); `assert_no_leaks(text)` raises on any hit. The scan is
      documented as a best-effort safeguard, not authorization to publish
      (ADR-0005): callers keep private-by-default regardless.
- [ ] Tests in `tests/test_capture.py` cover: each preset's resolved
      levels; overrides beating the preset; default-when-absent;
      fail-closed on malformed config; the two-opt-in session guard
      (neither opt-in alone yields public); leak detection of each
      category and a clean-text pass.
- [ ] `uv run agentmarshal validate`, pytest, ruff, and mypy stay green.

## Non-Goals

- No wiring into forward capture, `record-session`, `submit-review`, or
  the backfill — those consume this policy in later CRs. CR-029 writes no
  artifact and stores nothing.
- No change to the record schema (CR-027) or the gate/status (CR-028).
- No new project-config required section: `capture` stays optional with an
  `attested` default, so existing projects are unaffected. No edit to
  `project.py`.
- The leak-scanner is best-effort pattern matching, not a guarantee; it
  does not replace the private-by-default rule.
