CR220-001 — `src/agentmarshal/switch_off.py:216` mistakes any indented line beginning `[` for a TOML table header. A valid parser-accepted `on` entry containing a multiline nested array is therefore truncated; the command opens a task, produces malformed TOML, and fails instead of replacing the entry as required.

CR220-002 — `src/agentmarshal/switch_off.py:424-501` interpolates filesystem paths directly into success and error output. A project path containing a forgeable character can create extra display lines, violating the acceptance requirement that every displayed value be escaped.

Acceptance coverage:

- Criterion 1 is met structurally: the archived proposal, design, ADDED delta specification, merged main specification, and tasks exist. All 17 scenario headings exactly correspond to docstrings in `tests/test_switch_off.py`.
- Criterion 2 is demonstrated for ordinary inputs by `test_the_opened_contract_names_the_extension_scopes_the_switches_file_and_accepts_the_switch_off`, `test_the_switches_entry_is_written_for_the_opened_task`, `test_a_missing_switches_file_is_created_with_format_and_the_switches_table`, and `test_the_paths_are_printed_and_nothing_is_committed`, but CR220-001 prevents full compliance.
- Criterion 3 is met by the name, reason, malformed-file, already-off, file-form, and parse-back scenario tests in `tests/test_switch_off.py`.
- Criterion 4 is met by `test_the_file_is_replaced_by_a_temporary_file_renamed_in_the_same_directory`, `test_a_failure_after_the_task_is_opened_names_the_task_on_one_line_and_exits_non_zero`, and `test_a_sidecar_refuses_saying_operational_tasks_are_not_available`.
- Criterion 5’s command surface is demonstrated by `test_the_extension_group_takes_switch_off_with_a_name_and_a_reason`; existing commands and stage/gate code are untouched, and the coordinator reports the full CI sequence passed. Its display-safety requirement is not fully met because of CR220-002; the existing display test covers only a malformed switch name, not paths.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "3ec206bf2102ac9aa68d7105fd10a94c6867f7f8",
  "verdict": "blocked",
  "findings": [
    "CR220-001",
    "CR220-002"
  ],
  "classes": {
    "CR220-001": "correctness",
    "CR220-002": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Targeted Python reproduction of a parser-accepted on entry containing a multiline nested array",
        "result": "The original parsed successfully; _entry_span returned (2, 4), and the rewritten text failed parse_switches with \"Expected ']' at the end of a table declaration\"."
      },
      {
        "what": "Compared archived delta scenario headings with test docstrings using rg",
        "result": "All 17 scenario names have matching test docstrings."
      },
      {
        "what": "Inspected every print and escape_for_display call in switch_off.py",
        "result": "Success paths at lines 499-501 and several diagnostic paths are printed without escape_for_display."
      }
    ],
    "read": [
      "task contract CR-220 and supplied diff",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/journal/open_task.py",
      "src/agentmarshal/journal/contracts.py",
      "tests/test_switch_off.py",
      "openspec/changes/archive/2026-10-24-extension-switch-off/",
      "openspec/specs/extension-stages/spec.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The coordinator reports it passed on the reviewed commit; uv is unavailable in this review snapshot."
      },
      {
        "what": "Independent Git commit verification",
        "why": "The supplied snapshot has no discoverable Git metadata."
      }
    ]
  },
  "evidence": {
    "CR220-001": "src/agentmarshal/switch_off.py:216; targeted reproduction: original parsed as Switch(state='on', task='CR-1'), span=(2, 4), rewritten parse raised SwitchesError for malformed TOML.",
    "CR220-002": "src/agentmarshal/switch_off.py:424, src/agentmarshal/switch_off.py:448, src/agentmarshal/switch_off.py:483, src/agentmarshal/switch_off.py:493, and src/agentmarshal/switch_off.py:499"
  }
}
AGENTMARSHAL_VERDICT_END
