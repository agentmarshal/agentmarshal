CR220-F1: `src/agentmarshal/switch_off.py:143-164` treats any symlink inside `.agentmarshal/extensions/` as a declared extension; `_run_off` consequently opens a task and writes a switch for it, contradicting the declared file/directory-form requirement and the symlink refusal at `src/agentmarshal/journal/extensions.py:485-510`.

Acceptance coverage: criterion 1 is met by the archived proposal, design, delta specification, synchronized main specification, and the 19 matching scenario docstrings in `tests/test_switch_off.py`; repository validation reportedly passed. Criterion 2 is demonstrated by `test_the_opened_contract_names_the_extension_scopes_the_switches_file_and_accepts_the_switch_off`, `test_the_switches_entry_is_written_for_the_opened_task`, `test_a_missing_switches_file_is_created_with_format_and_the_switches_table`, `test_the_paths_are_printed_and_nothing_is_committed`, and the rewrite-preservation tests. Criterion 3 is not fully met because of CR220-F1; its reason, malformed-file, already-off, and file-form cases are otherwise demonstrated by the corresponding tests at `tests/test_switch_off.py:172-239`. Criterion 4 is demonstrated by the parse-back, same-directory rename, post-open failure, and sidecar tests at `tests/test_switch_off.py:381-505`. Criterion 5 is demonstrated by the command-surface and display-escaping tests at `tests/test_switch_off.py:478-569`, the existing trust/untrust/list regression tests, and the coordinator-reported full CI pass.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4c0fffb0cbed38a1f3f194664e9d08d71da9d9e0",
  "verdict": "changes_required",
  "findings": [
    "CR220-F1"
  ],
  "classes": {
    "CR220-F1": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Compared delta-spec scenario headings with test docstrings using rg",
        "result": "All 19 scenarios have correspondingly named test docstrings."
      },
      {
        "what": "Inspected the archived change and active extension-stages specification",
        "result": "The proposal, design, tasks, ADDED requirements, archive location, and synchronized requirements are present."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-220/contract.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/journal/extensions.py",
      "src/agentmarshal/journal/open_task.py",
      "tests/test_switch_off.py",
      "tests/test_extension_trust.py",
      "openspec/changes/archive/2026-10-24-extension-switch-off/specs/extension-stages/spec.md",
      "openspec/specs/extension-stages/spec.md"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "The coordinator reports it passed on the reviewed commit, and uv is unavailable in this review environment."
      },
      {
        "what": "Focused end-to-end symlink reproduction",
        "why": "The read-only environment provides no writable temporary directory; the finding follows directly from the unconditional symlink admission and subsequent membership check."
      },
      {
        "what": "Independent Git commit/diff verification",
        "why": "The supplied snapshot contains no discoverable .git metadata."
      }
    ]
  },
  "evidence": {
    "CR220-F1": "src/agentmarshal/switch_off.py:143 adds every symlink entry to the declared-name set, and src/agentmarshal/switch_off.py:600 accepts membership without calling the manifest reader; src/agentmarshal/journal/extensions.py:485-510 instead refuses symlinked manifest paths."
  }
}
AGENTMARSHAL_VERDICT_END
