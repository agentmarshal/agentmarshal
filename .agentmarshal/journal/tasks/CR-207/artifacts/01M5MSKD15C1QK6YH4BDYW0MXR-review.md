CR207-001 — `templates/journal-transaction.sh:83` destroys NUL-delimited status boundaries by translating them to newlines. A foreign filename containing `\n?? .agentmarshal/journal/tasks/CR-001/…` is split into two apparent records, and the suffix is incorrectly suppressed as belonging to the selected task. Thus the script does not list every other changed path, violating acceptance criterion 2.

Acceptance criterion 1 is met by the literal pathspec, branch, commit, push, and pull-request guidance; `test_the_transaction_takes_only_its_own_tasks_journal_directory` and `test_the_push_goes_to_the_remote_am_remote_names` exercise these behaviors. Criterion 2 is met for ordinary paths and refusals by `test_the_transaction_takes_only_its_own_tasks_journal_directory`, `test_refusals_stage_nothing_and_name_the_reason`, and the rename/deep-path tests, but fails for newline-bearing paths as CR207-001 describes. Criterion 3 is met by `src/agentmarshal/project.py` and `test_outbox_readme_excludes_non_evidence_from_journal_staging`; the outbox specification does not pin the replaced command, so its OpenSpec condition does not apply. Criterion 4 is met by direct inspection of the quickstart, sidecar guide, and both proposal Where sections; there is no dedicated documentation test. Criterion 5 is supported by the coordinator’s recorded full-CI pass on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "bc929a76867b70a0ec92543c5a288282ebac6851",
  "verdict": "changes_required",
  "findings": [
    "CR207-001"
  ],
  "classes": {
    "CR207-001": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "sh -n templates/journal-transaction.sh",
        "result": "passed"
      },
      {
        "what": "Replay lines 81-117's parser with a NUL-terminated foreign path containing a newline followed by an own-task-looking suffix",
        "result": "output contained only '?? .agentmarshal/journal/other/foreign'; the remainder of the filename was suppressed"
      }
    ],
    "read": [
      "Task contract and supplied diff",
      "templates/journal-transaction.sh",
      "tests/test_journal_transaction.py",
      "src/agentmarshal/project.py and tests/test_project.py",
      "docs/quickstart.md",
      "docs/sidecar.md",
      "docs/proposals/019-journal-transactions-assume-direct-commits.md",
      "docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md",
      "docs/adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md",
      "docs/threat-model.md",
      "openspec/specs/outbox/spec.md",
      "openspec/specs/record-text-safety/spec.md",
      "Coordinator's full-CI pass statement for bc929a76867b70a0ec92543c5a288282ebac6851"
    ],
    "not_run": [
      {
        "what": "Targeted pytest suite and full CI sequence",
        "why": "uv is unavailable and the system Python has no pytest; the coordinator states the full sequence passed on the reviewed commit"
      },
      {
        "what": "Full temporary-repository reproduction of CR207-001",
        "why": "the review filesystem, including /tmp, is read-only; the exact parser was reproduced using a synthetic porcelain byte stream"
      }
    ]
  },
  "evidence": {
    "CR207-001": "templates/journal-transaction.sh:83 converts NUL separators to newlines before record parsing. Parser replay with `printf '?? .agentmarshal/journal/other/foreign\\n?? .agentmarshal/journal/tasks/CR-001/hidden.json\\0'` printed only `?? .agentmarshal/journal/other/foreign`. openspec/specs/record-text-safety/spec.md:130-147 confirms newline-bearing Git paths are supported inputs."
  }
}
AGENTMARSHAL_VERDICT_END
