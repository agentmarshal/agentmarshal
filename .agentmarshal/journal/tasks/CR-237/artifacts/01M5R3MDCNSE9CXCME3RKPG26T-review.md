F1 — `report.py:569–571` checks only the accepted tip’s writers, so it omits `self-accepted` when the accepting party wrote an earlier commit in the candidate range. The gate marks that same acceptance. `test_a_writer_of_an_earlier_range_commit_is_marked_by_the_gate_alone` explicitly asserts this disagreement at lines 373–384. This breaks acceptance criterion 1 and ADR-0007 decision 4; the new delta documents an exception the contract does not authorize.

Acceptance assessment:

- **Criterion 1: partially met.** Gate qualification and tip-writer report marking are demonstrated by `test_the_gates_acceptance_line_marks_a_self_acceptance` and `test_reports_task_line_marks_a_self_acceptance`. F1 leaves range-writer marking incomplete.
- **Criterion 2: met.** `_task_report` selects records preceding completion and matching its binding. Tests cover earlier-commit acceptance followed by approval, same-commit approval, and completion over findings.
- **Criterion 3: structurally met.** The archived delta contains MODIFIED and ADDED requirements; all 18 scenarios have matching test docstrings. The MODIFIED text appears verbatim in the main spec. Archive-command execution was not independently verified.
- **Criterion 4: supported.** Unmarked output is pinned by `test_an_acceptance_by_another_party_prints_unmarked` and `test_every_output_for_an_acceptance_over_findings_is_unchanged`; escaping remains covered by the display and gate tests. The coordinator reports all six CI checks passed. I could not rerun them here.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b97616415ebe49856c797681f0170bf016f86ba8",
  "verdict": "changes_required",
  "findings": ["F1"],
  "classes": {
    "F1": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Read-only Python AST inspection of delta scenarios and test docstrings",
        "result": "18/18 scenarios matched"
      },
      {
        "what": "Compare archived MODIFIED requirement with main specification",
        "result": "Present verbatim"
      },
      {
        "what": "Compile changed Python source files in memory",
        "result": "Passed"
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-237/contract.md",
      "CONTRIBUTING.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0007-operator-acceptance.md",
      "Supplied diff, changed source files, archived change artifacts, operator-acceptance specification, and relevant tests"
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "uv and test/check packages are unavailable in this read-only snapshot. Coordinator reports the sequence passed on the reviewed commit."
      }
    ]
  },
  "evidence": {
    "F1": "src/agentmarshal/journal/report.py:569–571 limits writer lookup to accepted_commit; tests/test_self_acceptance_on_every_surface.py:364–384 constructs Alice's earlier range commit followed by Bob's tip, asserts the gate marks Alice's acceptance, and asserts report omits the mark. Contract acceptance criterion 1 requires both surfaces to mark a declared candidate writer."
  }
}
AGENTMARSHAL_VERDICT_END
