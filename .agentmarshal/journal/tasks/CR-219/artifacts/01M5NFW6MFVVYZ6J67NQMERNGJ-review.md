Blocked by one acceptance-breaking correctness defect.

CR219-RAW-EQUALITY — `src/agentmarshal/journal/gate.py:1376-1389` compares parsed TOML with Python equality, under which integer `1` equals float `1.0`; therefore an extra entry field can change type while retaining another task’s `task`, yet `misnamed` remains empty and the operational lane may pass. This violates acceptance criterion 2’s requirement that every changed entry name the current task. The existing test at `tests/test_gate_operational.py:451` only compares distinct strings and misses this collision.

Acceptance coverage:

- Criterion 1 is met: the proposal, design, archived ADDED/MODIFIED delta specs, and synchronized main specs exist. Static extraction matched all 34 delta scenarios to exact test docstrings.
- Criterion 2 is demonstrated for ordinary additions, removals, re-enabling, malformed bases, and foreign tasks by `tests/test_gate_operational.py`, but is not fully met because of CR219-RAW-EQUALITY.
- Criterion 3 is demonstrated by `test_an_extra_path_in_the_diff_takes_the_lane_it_takes_today`, `test_a_malformed_switches_file_at_the_candidate_refuses_naming_the_file`, and `test_in_a_sidecar_the_operational_lane_is_not_offered`.
- Criterion 4 is demonstrated by `test_pre_gate_stages_do_not_run_on_an_operational_change` and `test_other_phases_and_other_candidates_behave_as_today`.
- Criterion 5 is demonstrated by the unchanged pinned transcript fixtures, `test_a_value_that_could_forge_a_line_is_escaped_on_display`, and the coordinator-reported full CI pass.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "c212ed966298b0996693a60e63167e6da4a95797",
  "verdict": "blocked",
  "findings": [
    "CR219-RAW-EQUALITY"
  ],
  "classes": {
    "CR219-RAW-EQUALITY": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "AST comparison of archived delta-spec scenario headings against test docstrings",
        "result": "34 scenarios found; all 34 had an exact matching Scenario docstring"
      },
      {
        "what": "python3 tomllib reproduction of the gate's entry comparison",
        "result": "base note: 1 int; candidate note: 1.0 float; entry equality: True; gate misnamed predicate: False"
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-219/contract.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0010-process-extensions.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "openspec/changes/archive/2026-10-24-gate-operational-lane/",
      "openspec/specs/gate-lanes/spec.md",
      "openspec/specs/extension-stages/spec.md",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/switches.py",
      "tests/test_gate_operational.py",
      "tests/test_gate.py",
      "tests/test_stages.py"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The supplied snapshot has no Git metadata and uv is unavailable; the coordinator reports the complete sequence passed on the reviewed commit."
      },
      {
        "what": "End-to-end temporary-repository reproduction",
        "why": "The read-only environment provides no writable temporary directory; the exact parsed-value comparison was reproduced directly."
      }
    ]
  },
  "evidence": {
    "CR219-RAW-EQUALITY": "src/agentmarshal/journal/gate.py:1376 and src/agentmarshal/journal/gate.py:1386; python3 reproduction output: int 1 versus float 1.0 produced entry equality True and gate misnamed predicate False"
  }
}
AGENTMARSHAL_VERDICT_END
