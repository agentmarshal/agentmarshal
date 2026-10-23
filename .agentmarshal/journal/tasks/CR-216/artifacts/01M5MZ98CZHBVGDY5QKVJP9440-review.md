CR216-001 — `src/agentmarshal/doctor.py:164` converts every matched component with `int()` without handling `ValueError`; a runtime reporting `v` followed by 5,000 digits crashes `doctor` instead of producing the required unreadable-version failure on the extension line. Acceptance 1 is met by the archived proposal, design, ADDED delta spec, synchronized main spec, and all 13 scenario-named tests in `tests/test_doctor_wrapper_runtime.py`; acceptance 2 is demonstrated by `test_a_wrappers_runtime_that_meets_the_declared_minimum_passes`, `test_each_wrapper_gets_its_own_runtime_check`, and the invocation-failure/timeout tests; acceptance 3 is demonstrated for ordinary inputs by the numeric-comparison, missing, failure, timeout, unreadable, and below-minimum tests, but is broken by this finding; acceptance 4 is demonstrated by the escaping, no-wraps, and unchanged-output tests; acceptance 5 is demonstrated by `test_the_check_runs_nothing_else_an_extension_declares_and_installs_nothing`, the temporary-PATH fixtures, the doctor-only source diff, and the coordinator’s passing full-CI report.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "96304ae2854e319c3636792c5c350eabec8715f2",
  "verdict": "changes_required",
  "findings": [
    "CR216-001"
  ],
  "classes": {
    "CR216-001": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B invoking _runtime_version('v' + '9' * 5000)",
        "result": "Raised ValueError: Exceeds the limit (4300 digits) for integer string conversion"
      },
      {
        "what": "Compared archived delta-spec scenario headings with test docstrings",
        "result": "All 13 scenarios have matching Scenario-named test docstrings"
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-216/contract.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/threat-model.md",
      "src/agentmarshal/doctor.py",
      "src/agentmarshal/journal/extensions.py",
      "tests/test_doctor_wrapper_runtime.py",
      "openspec/changes/archive/2026-10-24-doctor-wrapper-runtime/",
      "openspec/specs/extension-manifest/spec.md"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The snapshot has no Git metadata or uv executable; the coordinator reports the complete sequence passed on the reviewed commit."
      }
    ]
  },
  "evidence": {
    "CR216-001": "src/agentmarshal/doctor.py:164; direct Python invocation raised ValueError for a 5,000-digit matched version component"
  }
}
AGENTMARSHAL_VERDICT_END
