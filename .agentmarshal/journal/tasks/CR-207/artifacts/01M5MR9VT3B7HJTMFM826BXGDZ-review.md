CR207-F1 — `templates/journal-transaction.sh` is mode `0644`, so the contract’s direct `journal-transaction.sh <task-id> <slug> <message-file>` invocation fails with exit 126. `tests/test_journal_transaction.py:103` masks this by explicitly invoking `sh`; ship the template executable and test direct execution.

Acceptance criterion 1 is otherwise demonstrated by `test_the_transaction_takes_only_its_own_tasks_journal_directory` and `test_the_push_goes_to_the_remote_am_remote_names`, but the file-mode defect leaves it unmet. Criterion 2 is met by the transaction and refusal tests. Criterion 3 is met by `test_outbox_readme_excludes_non_evidence_from_journal_staging`; the outbox specification does not pin the replaced text, so no OpenSpec change was required. Criterion 4 is met by the updated guides and dated proposal sections; `test_the_main_path_prints_the_documented_gate_transcript` exercises the quickstart commands. Criterion 5 is met by the coordinator’s passing full-CI result on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "06b69b0ad05e03587ea13030f13564511dc21ecc",
  "verdict": "changes_required",
  "findings": [
    "CR207-F1"
  ],
  "classes": {
    "CR207-F1": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "stat -c '%A %a %n' templates/journal-transaction.sh",
        "result": "-rw-r--r-- 644 templates/journal-transaction.sh"
      },
      {
        "what": "./templates/journal-transaction.sh CR-001 slug message.txt",
        "result": "Direct invocation failed with exit status 126"
      },
      {
        "what": "sh -n templates/journal-transaction.sh",
        "result": "Passed"
      },
      {
        "what": "Static searches of documented staging recipes and OpenSpec requirements",
        "result": "Per-task recipes are present; no outbox requirement pins the replaced README text"
      }
    ],
    "read": [
      "CR-207 contract and supplied diff",
      "templates/journal-transaction.sh",
      "tests/test_journal_transaction.py",
      "tests/test_project.py",
      "tests/test_quickstart.py",
      "src/agentmarshal/project.py",
      "docs/quickstart.md",
      "docs/sidecar.md",
      "docs/proposals/019-journal-transactions-assume-direct-commits.md",
      "docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md",
      "docs/adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md",
      "docs/threat-model.md",
      "openspec/specs/outbox/spec.md",
      "coordinator's passing full-CI report for commit 06b69b0ad05e03587ea13030f13564511dc21ecc"
    ],
    "not_run": [
      {
        "what": "Full repository CI sequence",
        "why": "The coordinator established that it passed on the exact reviewed commit; this snapshot has no uv or Python executable"
      },
      {
        "what": "Independent commit and parent-diff inspection",
        "why": "The supplied snapshot contains no Git metadata"
      }
    ]
  },
  "evidence": {
    "CR207-F1": "templates/journal-transaction.sh has mode 0644; direct execution exited 126, while tests/test_journal_transaction.py:103 invokes it as ['sh', str(SCRIPT), *arguments]"
  }
}
AGENTMARSHAL_VERDICT_END
