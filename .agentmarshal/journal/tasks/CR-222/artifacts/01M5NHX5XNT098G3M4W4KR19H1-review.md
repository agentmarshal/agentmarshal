CR222-001: `src/agentmarshal/cli.py:1282-1289` enumerates extensions before checking whether `switches.toml` exists, so an enumeration refusal emits `switches: unavailable (...)` even when the file is absent, contradicting acceptance criterion 3 and the archived spec at `openspec/specs/extension-stages/spec.md:28-30`; the existing missing-file test uses a normal extension directory and misses this case. Acceptance criterion 1 is met by the archived proposal/design/delta and the ten scenario-named tests in `tests/test_status_switches.py:68-270`; criterion 2 is demonstrated by the listing, single-task, escaping, and link tests there; criterion 4 is demonstrated by `test_doctor_enumerates_through_the_shared_function` plus the existing doctor suite; criterion 5 is supported by the scoped diff and the coordinator-confirmed full CI pass on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "719c3614f20b5a5d7834193bead3b8707f1835ff",
  "verdict": "changes_required",
  "findings": [
    "CR222-001"
  ],
  "classes": {
    "CR222-001": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "PYTHONPATH=src python3 -m agentmarshal brief --task CR-222",
        "result": "Succeeded; printed the contract, named decisions, and extension-stages specification."
      },
      {
        "what": "Unit-level invocation of _print_switched_off with extension enumeration raising before read_switches",
        "result": "Produced 'switches: unavailable (cannot enumerate extensions)\\n', confirming the exception path emits output before file absence can be handled."
      },
      {
        "what": "git status --short && git rev-parse HEAD",
        "result": "Git metadata is absent from the supplied snapshot, so HEAD could not be resolved independently."
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
      "tests/test_status_switches.py",
      "tests/test_doctor_extensions.py",
      "openspec/changes/archive/2026-10-24-status-shows-switches/",
      "openspec/specs/extension-stages/spec.md"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The coordinator reports it passed on the exact reviewed commit; uv is unavailable in this read-only snapshot."
      }
    ]
  },
  "evidence": {
    "CR222-001": "The spec requires no new stderr when switches.toml is absent at openspec/specs/extension-stages/spec.md:28-30, but src/agentmarshal/cli.py:1282-1289 calls _managed_directory/shared_extension_names first and reports any resulting exception; the unit-level check produced 'switches: unavailable (cannot enumerate extensions)'."
  }
}
AGENTMARSHAL_VERDICT_END
