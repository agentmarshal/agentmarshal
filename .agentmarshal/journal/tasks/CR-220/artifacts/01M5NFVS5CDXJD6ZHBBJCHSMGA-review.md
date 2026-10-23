No blocking or advisory findings.

Acceptance criteria are met:

- The archived proposal, design, ADDED delta specification, and synchronized main specification are present. All 22 scenarios match test docstrings in `tests/test_switch_off.py`.
- Task creation, exact scope, switch writing, content preservation, path output, and no commit are demonstrated by `test_the_opened_contract...`, `test_the_switches_entry...`, `test_an_existing_on_entrys_table...`, and `test_the_paths_are_printed_and_nothing_is_committed`.
- Pre-write validation, broken/link-form extension handling, malformed files, already-off refusal, and parser round-trip are covered by the corresponding validation tests and `test_the_new_text_is_parsed_back_before_it_replaces_the_file`.
- Atomic replacement, post-open failure reporting, and sidecar refusal are demonstrated by `test_the_file_is_replaced...`, `test_a_failure_after_the_task_is_opened...`, and `test_a_sidecar_refuses...`.
- Display escaping is covered by `test_a_value_that_could_forge_a_line_is_escaped_on_display` and `test_every_path_the_command_prints_is_escaped_on_display`; existing trust/untrust/list behavior remains covered by `tests/test_extension_trust.py`. The coordinator confirms the full CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "d3d3a05c0f2b531c737398779203bd493bd75193",
  "verdict": "approved",
  "findings": [],
  "verification": {
    "executed": [
      {
        "what": "Pure-Python delta-scenario/docstring comparison",
        "result": "All 22 scenario headings matched test docstrings."
      },
      {
        "what": "Pure-Python TOML rewrite probes for LF, CRLF, and quoted-key inputs",
        "result": "Each rewrite parsed and verified successfully."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-220/contract.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/doctor.py",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/journal/open_task.py",
      "tests/test_switch_off.py",
      "openspec/changes/archive/2026-10-24-extension-switch-off/",
      "openspec/specs/extension-stages/spec.md"
    ],
    "not_run": [
      {
        "what": "Focused pytest and the repository CI sequence",
        "why": "The review image has no uv executable; the coordinator states the full sequence passed on the reviewed commit."
      },
      {
        "what": "python3 -m compileall",
        "why": "The read-only snapshot prevents creation of __pycache__ files."
      },
      {
        "what": "git commit verification and status inspection",
        "why": "The supplied snapshot contains no .git directory."
      }
    ]
  }
}
AGENTMARSHAL_VERDICT_END
