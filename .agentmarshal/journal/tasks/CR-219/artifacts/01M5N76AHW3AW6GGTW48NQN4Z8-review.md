CR219-001 — `src/agentmarshal/journal/gate.py:1297-1313` discards every base switch when any base entry fails parsing, so a candidate may remove valid base entries without refusal; `test_a_removed_entry_is_refused_naming_the_file_and_the_entry` covers only a fully parseable base and does not demonstrate the unconditional removal rule required by acceptance criterion 2.

Acceptance criterion coverage:

- AC1 is met: the archived proposal, design, ADDED delta specification, and tasks exist; all 15 scenarios have correspondingly named docstrings in `tests/test_gate_operational.py`.
- AC2 is demonstrated for lane selection, contract source, transcript, task attribution, valid-base removal, switch-on, and unchanged entries by the corresponding operational-gate tests, but is not fully met because of CR219-001.
- AC3 is met by `test_an_extra_path_in_the_diff_takes_the_lane_it_takes_today`, the malformed/undeclared/wrong-task tests, and `test_in_a_sidecar_the_operational_lane_is_not_offered`.
- AC4 is met by `test_pre_gate_stages_do_not_run_on_an_operational_change` and `test_other_phases_and_other_candidates_behave_as_today`; `stages.py` imports the gate predicate.
- AC5 is met by the existing pinned transcript tests and `test_a_value_that_could_forge_a_line_is_escaped_on_display`; the coordinator reports the complete CI sequence passed at the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "42641d859dceb06a5693fd8f2ac4b0cfca464fda",
  "verdict": "blocked",
  "findings": [
    "CR219-001"
  ],
  "classes": {
    "CR219-001": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "Direct source and specification inspection with rg and sed",
        "result": "Confirmed the base SwitchesError handler replaces the complete base map with an empty map before removal comparison; confirmed no test covers a partially valid but globally refused base file."
      },
      {
        "what": "git rev-parse/show for reviewed commit",
        "result": "Unavailable because the supplied snapshot has no .git directory."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-219/contract.md",
      "src/agentmarshal/journal/gate.py",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/switches.py",
      "tests/test_gate_operational.py",
      "tests/test_gate.py",
      "openspec/changes/archive/2026-10-24-gate-operational-lane/",
      "openspec/specs/gate-lanes/spec.md",
      "openspec/specs/extension-stages/spec.md",
      "docs/adr/ADR-0010-process-extensions.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The coordinator established that it passed on the reviewed commit; this snapshot also lacks the uv executable."
      },
      {
        "what": "Dynamic temporary-repository reproduction",
        "why": "The read-only environment provides no writable temporary directory; the failing path is directly evident from the inspected control flow."
      }
    ]
  },
  "evidence": {
    "CR219-001": "src/agentmarshal/journal/gate.py:1297 — any SwitchesError reading the base assigns base_switches = {}; src/agentmarshal/journal/gate.py:1311 then computes removed only from that emptied mapping, contrary to contract.md acceptance criterion 2."
  }
}
AGENTMARSHAL_VERDICT_END
