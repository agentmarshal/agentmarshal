Acceptance criterion 1 is met: [commits.py](/tmp/agentmarshal-review-ybcfjv7a/snapshot/src/agentmarshal/commits.py:30) contains the sole scoped resolver, and all four callers translate `CommitResolutionError` into their existing error class. `tests/test_commits.py` demonstrates resolution behavior, while the existing command suites exercise each integration.

Acceptance criterion 2 is met: the previous messages are preserved byte-for-byte, including escaped Git stderr and launch failures. `tests/test_commits.py` covers full and abbreviated IDs, non-commit objects, unknown names, repository wording, escaping, and Git startup failure. The mocked resolver probe additionally verified the exact argv and messages.

Acceptance criterion 3 is met: `test_in_a_sidecar_the_pause_commit_resolves_in_the_journal_repository` and `test_in_a_sidecar_the_operational_commit_resolves_in_the_journal_repository` record the sidecar’s full HEAD, reject a host-only commit, and verify the journal remains unchanged after rejection.

Acceptance criterion 4 is met: the supplied diff changes only scoped paths, introduces no OpenSpec change, and is consistent with ADR-0013 and ADR-0022. The coordinator reports the complete CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "882d5c5eed1ec150e7134e26a23f2acd64110cbc",
  "verdict": "approved",
  "findings": [],
  "verification": {
    "executed": [
      {
        "what": "In-memory mocked probe of agentmarshal.commits.resolve_commit",
        "result": "Passed: verified exact argv without a shell, caller-selected repository wording, escaped stderr/reference text, 40-character enforcement, and cannot-run-git message."
      },
      {
        "what": "AST parse of the five changed source modules and two changed test files",
        "result": "Passed for all seven files."
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-218/contract.md and amendment record",
      "Supplied diff for commit 882d5c5eed1ec150e7134e26a23f2acd64110cbc",
      "src/agentmarshal/commits.py and all four scoped callers",
      "tests/test_commits.py and relevant command/sidecar tests",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md",
      "Coordinator note reporting the full CI sequence passed on the reviewed commit"
    ],
    "not_run": [
      {
        "what": "Focused pytest suites and local full CI sequence",
        "why": "The review image has no uv executable; the attempted command could not start. The coordinator independently reports the full sequence passed on the exact reviewed commit."
      },
      {
        "what": "Git parent comparison",
        "why": "The supplied snapshot contains no Git metadata; review used the supplied diff and candidate files."
      }
    ]
  }
}
AGENTMARSHAL_VERDICT_END
