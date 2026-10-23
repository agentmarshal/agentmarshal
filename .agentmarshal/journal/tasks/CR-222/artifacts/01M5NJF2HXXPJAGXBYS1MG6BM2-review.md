No blocking or advisory findings.

Acceptance criteria are met:

- Archived proposal, design, tasks, and ADDED delta requirements are present; all ten scenarios exactly match test docstrings in `tests/test_status_switches.py`.
- Status listing and task views are covered by the listing, single-task, early-return, escaping, and symlink tests.
- Unchanged stdout, absent/on switches, and parse-refusal behavior are covered by dedicated status tests and existing byte-exact status tests.
- Doctor uses `shared_extension_names` at both sites; the spy test and existing doctor extension tests demonstrate unchanged behavior.
- The supplied diff stays within scope, and the coordinator reports the complete CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "fb59707e344495942f97cacfca707759446236ec",
  "verdict": "approved",
  "findings": [],
  "verification": {
    "executed": [
      {
        "what": "Static inspection with rg, nl, find, and sed over the contract, implementation, archived OpenSpec artifacts, specifications, ADRs, threat model, and tests",
        "result": "Implementation and test coverage match all acceptance criteria; all ten delta scenarios have exactly named test docstrings."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-222/contract.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/threat-model.md",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/doctor.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/journal/display.py",
      "tests/test_status_switches.py",
      "tests/test_status_steps.py",
      "tests/test_status_view.py",
      "tests/test_doctor_extensions.py",
      "openspec/changes/archive/2026-10-24-status-shows-switches/proposal.md",
      "openspec/changes/archive/2026-10-24-status-shows-switches/design.md",
      "openspec/changes/archive/2026-10-24-status-shows-switches/tasks.md",
      "openspec/changes/archive/2026-10-24-status-shows-switches/specs/extension-stages/spec.md",
      "openspec/specs/extension-stages/spec.md"
    ],
    "not_run": [
      {
        "what": "Focused pytest run and full CI sequence",
        "why": "The review container has neither uv nor python; uv exited 127 with '/bin/bash: uv: command not found'. The coordinator reports the full sequence passed on the exact reviewed commit."
      },
      {
        "what": "Independent Git commit and diff verification",
        "why": "The supplied snapshot contains no discoverable .git metadata; review used the supplied commit SHA, supplied diff, and candidate files."
      }
    ]
  }
}
AGENTMARSHAL_VERDICT_END
