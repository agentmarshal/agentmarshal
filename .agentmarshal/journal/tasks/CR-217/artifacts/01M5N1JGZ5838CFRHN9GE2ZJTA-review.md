CR217-001: `src/agentmarshal/stages.py:645-652` reads and validates `trust.toml` before handling switched-off outcomes; on a workstation, malformed grant state aborts without the required switched-off result, despite the requirement that switched-off stages are not grant-checked.

CR217-002: `src/agentmarshal/stages.py:611-613` returns before reading the base switches file when the requested phase has no stages, so a malformed base file is neither read nor reported as required.

Acceptance criterion 1 is met: the archived proposal, design, ADDED delta specification, and tasks are present; all 20 scenarios have matching docstrings in `tests/test_switches.py` (the base-reading scenario has two tests). Criterion 2 is met by the six parser tests from `test_an_off_switch_parses_with_its_task_and_reason` through `test_a_switch_entry_outside_its_shape_is_refused_naming_the_file_and_the_entry`. Criterion 3 is not fully met because of CR217-001 and CR217-002; its normal CI paths are otherwise covered by the stage tests in `tests/test_switches.py`. Criterion 4 is met by the six doctor tests beginning with `test_doctor_shows_a_switched_off_extension_with_its_task_and_reason`. Criterion 5 is met by `test_a_value_that_could_forge_a_line_is_escaped_on_display`, parser rejection tests, inspection showing no gate changes, and the coordinator-confirmed full CI pass.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "64862b0b788bdcdef623338af36986b913ac9e08",
  "verdict": "blocked",
  "findings": [
    "CR217-001",
    "CR217-002"
  ],
  "classes": {
    "CR217-001": "correctness",
    "CR217-002": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Static scenario/docstring comparison with rg",
        "result": "20 delta-spec scenarios and 21 matching scenario docstrings; the base-reading scenario intentionally has two tests."
      },
      {
        "what": "Stubbed non-CI _run_stages invocation with an off switch and malformed trust file",
        "result": "exit=1, stdout='', stderr='stage run: /local/trust.toml: malformed\\n'"
      },
      {
        "what": "Stubbed _run_stages invocation with no stage in the requested phase and malformed _base_switches",
        "result": "exit=0, stdout='stage run: no shared extension declares a pre-gate stage\\n', stderr=''; _base_switches was not called."
      }
    ],
    "read": [
      "supplied CR-217 contract and diff",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md",
      "openspec/changes/archive/2026-10-24-shared-extension-switches/",
      "openspec/specs/extension-stages/spec.md",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/doctor.py",
      "tests/test_switches.py"
    ],
    "not_run": [
      {
        "what": "Full CI sequence and focused pytest suite",
        "why": "The snapshot lacks uv and pytest; the coordinator states the full sequence passed on the reviewed commit."
      },
      {
        "what": "Independent Git commit/diff verification",
        "why": "The supplied snapshot contains no Git metadata."
      }
    ]
  },
  "evidence": {
    "CR217-001": "Stubbed command output: exit=1, stdout='', stderr='stage run: /local/trust.toml: malformed\\n'; controlling code is src/agentmarshal/stages.py:645.",
    "CR217-002": "Stubbed command output: exit=0 with only 'stage run: no shared extension declares a pre-gate stage'; early return is src/agentmarshal/stages.py:611."
  }
}
AGENTMARSHAL_VERDICT_END
