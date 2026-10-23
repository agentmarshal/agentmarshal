CR217-F1 — `parse_switches` treats an existing file containing only `format = 1` as valid because [switches.py:99](/tmp/agentmarshal-review-jq0ms3jt/snapshot/src/agentmarshal/switches.py:99) defaults the absent `switches` table to `{}`; the archived requirement says the file SHALL carry a `[switches]` table and malformed files must be refused.

CR217-F2 — When both the base switches file and workstation trust file are malformed, [stages.py:752](/tmp/agentmarshal-review-jq0ms3jt/snapshot/src/agentmarshal/stages.py:752) skips the stage before the `blocked_names` branch, suppressing the required `not run (shared switches file unreadable)` result from [the specification](/tmp/agentmarshal-review-jq0ms3jt/snapshot/openspec/specs/extension-stages/spec.md:442) and contradicting ADR-0013 decision 7’s no-silence rule.

Acceptance coverage:

1. The proposal, design, delta specification, tasks, archive, and main-spec synchronization are present. All 20 delta scenarios have matching test docstrings in `tests/test_switches.py`; an AST comparison found none missing.
2. Parser behavior is demonstrated by `test_an_off_switch_parses_with_its_task_and_reason`, `test_a_file_that_is_not_toml_is_refused_naming_it`, `test_an_unknown_or_missing_format_is_refused_naming_the_file`, and the entry-shape tests, except for CR217-F1.
3. Base-only reading, switched-off results, non-execution, events, and non-pausing are demonstrated by the stage tests beginning at [test_switches.py:170](/tmp/agentmarshal-review-jq0ms3jt/snapshot/tests/test_switches.py:170); malformed-switch behavior is covered at lines 328 and 379, except for CR217-F2’s combined malformed-trust path.
4. Doctor’s working-tree display, missing-file behavior, file-form behavior, and malformed-file reporting are demonstrated by the tests beginning at [test_switches.py:500](/tmp/agentmarshal-review-jq0ms3jt/snapshot/tests/test_switches.py:500).
5. Display escaping is demonstrated by `test_a_value_that_could_forge_a_line_is_escaped_on_display`; the supplied diff leaves the gate and other commands unchanged. The coordinator reports the full CI sequence passed at the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "07db3a3bcc6def6d65b7ecde47d3896b72e8ae6d",
  "verdict": "changes_required",
  "findings": [
    "CR217-F1",
    "CR217-F2"
  ],
  "classes": {
    "CR217-F1": "contract-mismatch",
    "CR217-F2": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -c \"from agentmarshal.switches import parse_switches; print(parse_switches(b'format = 1\\n', 'switches.toml', {'openspec'}))\"",
        "result": "Returned {}, confirming that an existing file without the required [switches] table is accepted."
      },
      {
        "what": "AST comparison of archived delta-spec scenario headings with tests/test_switches.py docstrings",
        "result": "20 scenarios found; missing_docstrings was empty."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-217/contract.md",
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
        "what": "Full CI sequence",
        "why": "uv and pytest are unavailable in the read-only snapshot; the coordinator reports that the sequence passed on the reviewed commit."
      },
      {
        "what": "Git commit/diff verification",
        "why": "The supplied snapshot has no Git metadata and reports 'not a git repository'."
      },
      {
        "what": "Dynamic combined malformed-switches/malformed-trust integration probe",
        "why": "The read-only environment exposes no writable temporary directory; the defect is established by the branch ordering at stages.py:752-761."
      }
    ]
  },
  "evidence": {
    "CR217-F1": "src/agentmarshal/switches.py:99-110 defaults a missing switches key to {}; the direct parser probe returned {}; openspec/specs/extension-stages/spec.md:381-395 requires the table.",
    "CR217-F2": "src/agentmarshal/stages.py:752-756 continues when grants_unreadable before reaching blocked_names at lines 757-761; openspec/specs/extension-stages/spec.md:442-446 requires every affected stage to report not run."
  }
}
AGENTMARSHAL_VERDICT_END
