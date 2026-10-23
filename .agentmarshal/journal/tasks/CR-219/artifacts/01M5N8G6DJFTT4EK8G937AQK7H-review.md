OPL-001 — `gate.py:1342-1347` compares reduced `Switch` objects, so a candidate can change an accepted extra field in an existing entry, retain another task’s `task`, and pass the operational lane; this violates acceptance criterion 2’s requirement that every changed entry name the current task.

IMP-001 — Directly importing `agentmarshal.switches` now fails at `gate.py:68` with a circular-import `ImportError`; normal CLI import order masks this regression, so it is advisory.

Acceptance criterion 1 is met: the archived proposal, design, tasks, and ADDED delta specification are present, the main specification is synchronized, and all 16 scenarios have named docstring tests in `tests/test_gate_operational.py`.

Acceptance criterion 2 is not fully met because of OPL-001. Its other cases are demonstrated by `test_the_operational_lane_admits_a_switches_only_candidate`, the base/candidate contract tests, scope test, malformed-base test, removal test, switch-on test, unchanged-entry test, and review-independent-check tests.

Acceptance criterion 3 is met by `test_an_extra_path_in_the_diff_takes_the_lane_it_takes_today`, the malformed/misnamed/undeclared-entry tests, and `test_in_a_sidecar_the_operational_lane_is_not_offered`.

Acceptance criterion 4 is met: `stages.py:574-592` imports and calls the gate predicate before extension manifests are read; `test_pre_gate_stages_do_not_run_on_an_operational_change` and `test_other_phases_and_other_candidates_behave_as_today` demonstrate both branches.

Acceptance criterion 5 is met for command behavior and CI: existing pinned transcript tests remain unchanged, escaping is tested by `test_a_value_that_could_forge_a_line_is_escaped_on_display`, and the coordinator reports the full CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "efe51da6dca396aacffa408d7045d26b508a0d60",
  "verdict": "changes_required",
  "findings": [
    "OPL-001"
  ],
  "advisory_findings": [
    "IMP-001"
  ],
  "classes": {
    "OPL-001": "contract-mismatch",
    "IMP-001": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "Parsed base and candidate switch entries differing only in an accepted extra field, then evaluated the gate's misnamed-entry predicate",
        "result": "parsed_equal: True; misnamed_predicate: False"
      },
      {
        "what": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -c 'from agentmarshal.switches import parse_switches'",
        "result": "ImportError: cannot import name 'SWITCHES_RELPATH' from partially initialized module 'agentmarshal.switches'"
      },
      {
        "what": "Compared archived delta-spec scenario headings with tests/test_gate_operational.py docstrings",
        "result": "All 16 scenario names are represented"
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
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/switches.py",
      "tests/test_gate_operational.py",
      "tests/test_gate.py",
      "tests/test_switches.py"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The supplied snapshot has no Git metadata and uv is unavailable locally; the coordinator states the full sequence passed on the reviewed commit."
      }
    ]
  },
  "evidence": {
    "OPL-001": "src/agentmarshal/switches.py:90 and :159 discard accepted extra entry keys, while src/agentmarshal/journal/gate.py:1342 compares only the resulting Switch objects; reproduction output: parsed_equal: True, misnamed_predicate: False",
    "IMP-001": "Direct-import command failed through src/agentmarshal/journal/gate.py:68 with a partially initialized agentmarshal.switches ImportError"
  }
}
AGENTMARSHAL_VERDICT_END
