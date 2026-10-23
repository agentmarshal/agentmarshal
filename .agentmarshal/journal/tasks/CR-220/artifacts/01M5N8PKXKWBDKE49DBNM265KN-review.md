CR220-001 (blocking): [switch_off.py:208](/tmp/agentmarshal-review-1ncap5wv/snapshot/src/agentmarshal/switch_off.py:208) recognizes only canonical textual key spellings, so valid TOML such as `["switch\u0065s".openspec]`, `"st\u0061te"`, or `"t\u0061sk"` is accepted by `parse_switches` but refused instead of rewriting an existing `on` entry, violating the second acceptance criterion and the archived requirement.

CR220-002 (blocking): [switch_off.py:584](/tmp/agentmarshal-review-1ncap5wv/snapshot/src/agentmarshal/switch_off.py:584) decodes existing bytes before calling `parse_switches`; invalid UTF-8 therefore raises an uncaught `UnicodeDecodeError` instead of refusing the malformed switches file by name, violating the third acceptance criterion.

Acceptance coverage:

- AC1 is met: proposal, design, ADDED delta requirements, tasks, archive, and merged specification are present. An AST/docstring audit matched all 19 scenarios to tests.
- AC2’s normal behavior is demonstrated by `test_the_opened_contract...`, `test_the_switches_entry...`, `test_a_missing_switches_file...`, `test_the_paths...`, and the rewrite tests, but CR220-001 leaves the criterion incomplete.
- AC3’s validation and parse-back paths are demonstrated by the name, reason, malformed-file, already-off, file-form, and `test_the_new_text_is_parsed_back...` tests, but CR220-002 leaves malformed non-UTF-8 input incomplete.
- AC4 is met by the atomic-rename, post-open failure, and sidecar tests.
- AC5 is met by the display-escaping tests and the coordinator-confirmed full CI run; the supplied diff does not change the gate or stage-run paths.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "2bfc2d1a0a723669934ce4d3eb39192e9189dd0c",
  "verdict": "changes_required",
  "findings": [
    "CR220-001",
    "CR220-002"
  ],
  "classes": {
    "CR220-001": "contract-mismatch",
    "CR220-002": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "In-memory parser/rewrite probe for escaped TOML key spellings",
        "result": "parse_switches accepted all three inputs, while the rewrite reported span=None or rewrite=False."
      },
      {
        "what": "In-memory _read_existing probe with bytes b'\\xff'",
        "result": "Raised UnicodeDecodeError instead of SwitchesError."
      },
      {
        "what": "AST comparison of archived scenario headings with test docstrings",
        "result": "scenarios=19 docstring_matches=19 missing=[]"
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-220/contract.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md",
      "openspec/changes/archive/2026-10-24-extension-switch-off/",
      "openspec/specs/extension-stages/spec.md",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/switch_off.py",
      "src/agentmarshal/switches.py",
      "src/agentmarshal/journal/extensions.py",
      "src/agentmarshal/journal/open_task.py",
      "tests/test_switch_off.py"
    ],
    "not_run": [
      {
        "what": "Full CI sequence",
        "why": "uv is unavailable in the review environment; the coordinator supplied a passing result for the reviewed commit."
      }
    ]
  },
  "evidence": {
    "CR220-001": "src/agentmarshal/switch_off.py:208-233 and :297-304; probe output: escaped table key span=None rewrite=False, escaped state/task keys rewrite=False after parse_switches accepted them.",
    "CR220-002": "src/agentmarshal/switch_off.py:575-584; probe output: UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0."
  }
}
AGENTMARSHAL_VERDICT_END
