CR220-001 — `src/agentmarshal/switch_off.py:226-233` mistakes a `[`-led continuation inside a valid multiline TOML value for the next table, so a parser-accepted `on` entry can be refused instead of being replaced; `tests/test_switch_off.py:468-508` explicitly permits that refusal, contrary to the requirement that an existing `on` table be replaced.

Acceptance coverage — Criterion 1 is met: the proposal, design, archived ADDED delta, and synchronized main specification exist; all 17 scenarios have exact matching docstrings in `tests/test_switch_off.py`. Criterion 2 is met only for ordinary tables, as demonstrated by `test_the_opened_contract_names_the_extension_scopes_the_switches_file_and_accepts_the_switch_off`, `test_the_switches_entry_is_written_for_the_opened_task`, `test_a_missing_switches_file_is_created_with_format_and_the_switches_table`, and `test_the_paths_are_printed_and_nothing_is_committed`; CR220-001 prevents full compliance. Criterion 3 is met by the undeclared-name, invalid-reason, malformed-file, already-off, file-form, and parse-back tests. Criterion 4 is met by `test_the_file_is_replaced_by_a_temporary_file_renamed_in_the_same_directory`, `test_a_failure_after_the_task_is_opened_names_the_task_on_one_line_and_exits_non_zero`, and `test_a_sidecar_refuses_saying_operational_tasks_are_not_available`. Criterion 5 is met by the command-parser and display-escaping tests plus the coordinator-supplied full-CI pass; the supplied diff leaves the gate and stage runner unchanged.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "497ee16c956fadc73e7be111c018ef0b17467fee",
  "verdict": "changes_required",
  "findings": [
    "CR220-001"
  ],
  "classes": {
    "CR220-001": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Static scenario-to-docstring comparison",
        "result": "17 specification scenarios and 17 exact matching Scenario docstrings"
      },
      {
        "what": "PYTHONPATH=src python3 probe of _entry_span, _switches_text, and _verify_rewrite with a valid on entry containing a multiline nested array",
        "result": "span=(4, 8); verification returned: the rewritten text is not TOML: Expected ']' at the end of a table declaration"
      },
      {
        "what": "git rev-parse HEAD",
        "result": "Unavailable: the supplied snapshot is not a Git worktree"
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-220/contract.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md",
      "openspec/changes/archive/2026-10-24-extension-switch-off/",
      "openspec/specs/extension-stages/spec.md",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/journal/open_task.py",
      "tests/test_switch_off.py"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The coordinator supplied a passing result for the reviewed commit; uv is unavailable in this snapshot environment."
      }
    ]
  },
  "evidence": {
    "CR220-001": "src/agentmarshal/switch_off.py:226; openspec/specs/extension-stages/spec.md:608; tests/test_switch_off.py:468; direct probe output: span=(4, 8), followed by verification='the rewritten text is not TOML: Expected \"]\" at the end of a table declaration'"
  }
}
AGENTMARSHAL_VERDICT_END
