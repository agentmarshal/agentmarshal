ADV-readme-sweeping-recipe — [README.md:127](/tmp/agentmarshal-review-_hmur9sl/snapshot/README.md:127) still recommends `git add .agentmarshal`, which can sweep records from concurrent tasks; this file is outside CR-207’s scope and explicit acceptance paths, so the inconsistency is advisory.

Acceptance criteria:

1. Met: branch creation, literal per-task staging, message-file commit, remote push, and PR guidance are covered by `test_the_transaction_takes_only_its_own_tasks_journal_directory` and `test_the_push_goes_to_the_remote_am_remote_names`.
2. Met: foreign records and all required refusals are covered by `test_the_transaction_takes_only_its_own_tasks_journal_directory`, `test_refusals_stage_nothing_and_name_the_reason`, and the rename/path-handling tests.
3. Met: the generated outbox README uses per-task staging and retains the exclusion; `test_outbox_readme_excludes_non_evidence_from_journal_staging` demonstrates it. The outbox specification does not pin the replaced wording, so no OpenSpec modification was required.
4. Met by direct inspection of the quickstart, sidecar guide, and both proposal Where sections; there is no dedicated documentation-content test.
5. Met: no command implementation changed except generated documentation text, and the coordinator reports the complete CI sequence passed on the exact reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "1009d947504fd12158feb0098ca74dd6aa872a04",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-readme-sweeping-recipe"
  ],
  "classes": {
    "ADV-readme-sweeping-recipe": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "bash -n templates/journal-transaction.sh",
        "result": "passed"
      },
      {
        "what": "repository-wide search for sweeping git-add recipes",
        "result": "found the remaining top-level README.md recipe at line 127; targeted quickstart, sidecar, and generated-outbox recipes use per-task paths"
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-207/contract.md",
      "templates/journal-transaction.sh",
      "tests/test_journal_transaction.py",
      "tests/test_project.py",
      "src/agentmarshal/project.py",
      "docs/quickstart.md",
      "docs/sidecar.md",
      "docs/proposals/019-journal-transactions-assume-direct-commits.md",
      "docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md",
      "docs/adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md",
      "docs/threat-model.md",
      "openspec/specs/outbox/spec.md",
      "README.md"
    ],
    "not_run": [
      {
        "what": "local pytest and full CI sequence",
        "why": "uv and python are unavailable in the supplied snapshot environment; the coordinator attests that the complete sequence passed on the exact reviewed commit"
      },
      {
        "what": "git show/status verification",
        "why": "the supplied snapshot contains no Git metadata"
      }
    ]
  },
  "evidence": {
    "ADV-readme-sweeping-recipe": "README.md:127 — `git add .agentmarshal && git commit -m \"open CR-001\"`"
  }
}
AGENTMARSHAL_VERDICT_END
