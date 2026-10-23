CR211-ENV-PATH — `src/agentmarshal/stages.py:409-414` deliberately ignores a caller’s `PATH` even when named in `isolation.env`, contradicting the coordinator’s protocol in `openspec/changes/archive/2026-10-24-extension-stage-run/design.md:107-110`, which explicitly says the caller’s named `PATH` is copied. The test at `tests/test_stages.py:757-795` asserts the contradictory behavior, so acceptance criterion 3 is not met.

Acceptance criterion coverage:

- AC1 is met: the proposal, design, delta, published specification, and archived changes exist. All 43 published scenarios have matching `Scenario:` test docstrings; the static heading/docstring comparison returned no missing scenarios.
- AC2 is met by `test_pre_gate_invokes_the_pre_gate_warn_and_pre_gate_stop_stages`, `test_post_gate_invokes_the_post_gate_stages`, `test_the_base_commits_code_runs_not_the_candidates_or_the_working_trees`, `test_the_command_runs_under_the_cores_interpreter_never_through_a_shell`, and the timeout tests.
- AC3’s snapshot, protocol-variable, declared-environment, and exit-status portions are demonstrated by `test_the_working_directory_is_a_snapshot_of_the_candidate_commit`, `test_the_environment_carries_the_protocol_variables_and_a_minimal_path`, `test_only_the_environment_variables_the_manifest_names_are_passed`, and `test_exit_status_zero_checks_and_any_other_fails`; the named-`PATH` contradiction above prevents full satisfaction.
- AC4 is met by the workstation grant tests, `test_in_ci_no_grant_is_needed`, the result-line and framing tests, and the two `extension-event` tests.
- AC5 is met by the five pause/warn/post-gate tests and `test_the_journal_is_untouched`. The coordinator reports that the full CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "0d2280b6446d9da95d0dab59ba995817422bd5a0",
  "verdict": "changes_required",
  "findings": [
    "CR211-ENV-PATH"
  ],
  "classes": {
    "CR211-ENV-PATH": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Static comparison of published scenario headings against tests/test_stages.py Scenario docstrings",
        "result": "All 43 published scenario headings had a matching test docstring."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-211/contract.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0010-process-extensions.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/cli.py",
      "tests/test_stages.py",
      "openspec/changes/archive/2026-10-24-extension-stage-run/design.md",
      "openspec/specs/extension-stages/spec.md"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The coordinator supplied its passing result for this exact commit; uv and pytest are unavailable in the review snapshot."
      }
    ]
  },
  "evidence": {
    "CR211-ENV-PATH": "openspec/changes/archive/2026-10-24-extension-stage-run/design.md:107-110 requires a caller PATH named in isolation.env to be copied, while src/agentmarshal/stages.py:409-414 skips PATH explicitly; tests/test_stages.py:757-795 asserts the conflicting implementation."
  }
}
AGENTMARSHAL_VERDICT_END
