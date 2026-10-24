CR233-ENABLE — `extension enable` fails on a valid switches file containing `format = 1`, `[switches.mycheck]`, and `state = "off"` without an explicit `[switches]` header. Removing the last entry also removes the implicit parent table; verification then rejects the rewrite at `src/agentmarshal/extension_trust.py:1154`. I reproduced exit 1 with no write attempted. Preserve an empty `[switches]` table when removing the last entry. This breaks acceptance criterion 4.

Acceptance coverage below refers to tests read, not rerun:

1. **Planning and archive:** The archived directory contains the proposal, design, ADDED delta and completed tasks. All 46 scenario titles match test docstrings. `tasks.md:71` records the archive command; its execution could not be independently verified.
2. **Personal execution:** `stages.py` discovers through `LocalState`, skips discovery in CI and reuses the shared execution machinery. Tests in `tests/test_personal_extensions.py:191`, `:268`, `:292`, `:443` and `:547` cover grant-free execution, CI exclusion, complete, marked pauses and collisions.
3. **Manifest restrictions and journal authority:** `extension_trust.py` rejects forbidden fields; doctor uses that reader; record-ext remains shared-only. Tests at `:575`, `:619`, `:953` and `:1110` cover these requirements.
4. **Switches:** CLI flags and personal switch commands are implemented. Tests at `:658`, `:679`, `:718`, `:758`, `:870`, `:891` and `:909` cover ordinary operation and shared-name refusal. CR233-ENABLE exposes an uncovered valid-file case.
5. **Compatibility and validation:** The diff leaves gate code unchanged. Tests at `:1020` and `:1549` cover absent-personal behavior and display escaping; existing stage/complete/doctor tests remain. The coordinator reports the full CI sequence passed. Local reruns were unavailable because the required tooling is absent.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "be83392147a0513da2ad4e2c721700e87d7bbc45",
  "verdict": "changes_required",
  "findings": ["CR233-ENABLE"],
  "classes": {
    "CR233-ENABLE": "correctness"
  },
  "verification": {
    "executed": [
      {
        "what": "Read-only Python scenario/docstring comparison",
        "result": "46 delta scenarios; zero missing matching test docstrings"
      },
      {
        "what": "In-memory _run_enable reproduction using actual parsing and rewrite logic, with filesystem boundaries mocked",
        "result": "Valid off switch parsed successfully; enable returned 1 with 'the rewritten text changed more than the named switch'; no write attempted"
      },
      {
        "what": "Git metadata and tooling availability checks",
        "result": "Snapshot has no Git metadata; uv, pytest, ruff and mypy unavailable"
      }
    ],
    "read": [
      ".agentmarshal/journal/tasks/CR-233/contract.md",
      "docs/threat-model.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "CONTRIBUTING.md",
      "Supplied diff and corresponding implementation/test files",
      "openspec/changes/archive/2026-10-25-personal-extensions/",
      "openspec/specs/extension-stages/spec.md",
      "src/agentmarshal/localstate.py",
      "src/agentmarshal/journal/extensions.py",
      "src/agentmarshal/record_ext.py"
    ],
    "not_run": [
      {
        "what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy",
        "why": "Required tooling unavailable; coordinator's reported CI pass is acknowledged without claiming an independent rerun"
      }
    ]
  },
  "evidence": {
    "CR233-ENABLE": "src/agentmarshal/extension_trust.py:1154 removes the last child table; :915 requires switches={} to remain. Input 'format = 1\\n\\n[switches.mycheck]\\nstate = \"off\"\\n' parses successfully, but _run_enable returns 1: 'the rewrite could not be verified: the rewritten text changed more than the named switch'."
  }
}
AGENTMARSHAL_VERDICT_END
