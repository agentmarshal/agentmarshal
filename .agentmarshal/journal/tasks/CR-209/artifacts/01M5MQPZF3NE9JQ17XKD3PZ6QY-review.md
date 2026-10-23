CR209-F1: `src/agentmarshal/extension_trust.py:279-283` accepts `format = true` and `format = 1.0` because Python equates both with integer `1`; therefore `trust`, `untrust`, and `list` do not fail closed as required. The test at `tests/test_extension_trust.py:709-732` omits these cases.

Acceptance review:

- AC1 meets the artifact and archive requirements. All 36 scenarios have matching test docstrings; the archived delta and main specification are synchronized. The coordinator reports `agentmarshal validate` passed.
- AC2 is demonstrated by the grant, whole-directory hash, re-grant, identity, symlink, non-regular-file, missing-extension, and extension-form tests in `test_extension_trust.py`.
- AC3 is demonstrated by the untrust tests, list-state/change-order tests, no-write test, and command-parser test.
- AC4 meets atomic replacement, local-state placement, event, and journal boundaries through the corresponding atomic-write, malformed-file, event, and journal tests. It does not meet the unknown-format requirement because of CR209-F1.
- AC5 is demonstrated by `test_no_file_in_the_extensions_directory_is_run` and `test_the_journal_is_untouched`; the coordinator reports the complete CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "f4889536b9951917dece74166dd427201cf149a5",
  "verdict": "changes_required",
  "findings": [
    "CR209-F1"
  ],
  "classes": {
    "CR209-F1": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Directly parsed representative trust files with _read_grants",
        "result": "format = true and format = 1.0 were ACCEPTED; format = 2 was refused"
      },
      {
        "what": "Compared delta-spec scenario headings with test docstrings using Python AST parsing",
        "result": "36 scenarios, none missing and none extra"
      },
      {
        "what": "Compared the archived delta specification with the main extension-trust specification",
        "result": "Content matched apart from the expected delta/main headings and formatting"
      }
    ],
    "read": [
      "Task contract CR-209 and supplied diff",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/cli.py",
      "tests/test_extension_trust.py",
      "openspec/changes/archive/2026-10-24-extension-trust-grants/",
      "openspec/specs/extension-trust/spec.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md",
      "Coordinator-provided full-CI pass for f4889536b9951917dece74166dd427201cf149a5"
    ],
    "not_run": [
      {
        "what": "Full CI sequence and pytest",
        "why": "The review environment has neither uv nor pytest; the coordinator reports the full sequence passed on the reviewed commit"
      },
      {
        "what": "Independent Git commit verification",
        "why": "The supplied review snapshot contains no Git metadata"
      }
    ]
  },
  "evidence": {
    "CR209-F1": "src/agentmarshal/extension_trust.py:279-283; direct reproduction output: `true ACCEPTED {}`, `1.0 ACCEPTED {}`, `1 ACCEPTED {}`, `2 REFUSED ExtensionTrustError ... unknown format 2`"
  }
}
AGENTMARSHAL_VERDICT_END
