CR211-MATERIALIZE-VALUEERROR — `src/agentmarshal/stages.py:280-281,344-347` lets `ValueError` from an invalid symlink target escape, so the stage receives no required `not run (...)` result line and no event.

CR211-PATH-OVERRIDE — `src/agentmarshal/stages.py:401-405` replaces the required minimal `PATH` when `isolation.env` includes `PATH`; the published requirement at `openspec/specs/extension-stages/spec.md:150-158` requires the minimal path independently of declared variables.

Acceptance review:

- AC1 is met: both changes are archived with proposal, design, delta spec, and tasks; all 43 published scenarios have matching `Scenario:` docstrings in `tests/test_stages.py`. The coordinator’s successful `agentmarshal validate` confirms the archived OpenSpec material validates.
- AC2 is met for normal materialization and execution, demonstrated by `test_the_base_commits_code_runs_not_the_candidates_or_the_working_trees`, `test_the_command_runs_under_the_cores_interpreter_never_through_a_shell`, and the timeout tests.
- AC3 is not fully met because a declared `PATH` replaces the minimal path. The normal case is demonstrated by `test_the_environment_carries_the_protocol_variables_and_a_minimal_path`, but that test does not declare `PATH`.
- AC4 is not fully met for malformed symlink blobs because materialization can abort before producing the required result line/event. Grant, CI, framing, and event behavior are otherwise demonstrated by the grant tests, `test_every_stage_gets_exactly_one_result_line`, and the extension-event tests.
- AC5 is met in covered paths, demonstrated by the five pause/warning tests and `test_the_journal_is_untouched`. The coordinator reports the full CI sequence passed on the reviewed commit.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "fb35d96edf18d2fc3d27287f2e8b6be4d161fc68",
  "verdict": "blocked",
  "findings": [
    "CR211-MATERIALIZE-VALUEERROR",
    "CR211-PATH-OVERRIDE"
  ],
  "classes": {
    "CR211-MATERIALIZE-VALUEERROR": "correctness",
    "CR211-PATH-OVERRIDE": "contract-mismatch"
  },
  "verification": {
    "executed": [
      {
        "what": "Compared all 43 published extension-stage scenario headings with Scenario docstrings in tests/test_stages.py",
        "result": "All 43 headings had matching docstrings."
      },
      {
        "what": "PYTHONPATH=src python3 probe of _prepare_extension with _materialize_directory raising ValueError",
        "result": "ValueError: embedded null byte escaped instead of returning a not-run preparation."
      },
      {
        "what": "PYTHONPATH=src python3 probe of _stage_env with isolation.env=('PATH',) and caller PATH=/caller/bin",
        "result": "Returned PATH=/caller/bin rather than the required minimal /usr/bin:/bin."
      }
    ],
    "read": [
      "Task contract CR-211 supplied in the review request",
      "docs/adr/ADR-0010-process-extensions.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "docs/adr/ADR-0014-where-things-live.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/threat-model.md",
      "src/agentmarshal/stages.py",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/journal/extensions.py",
      "src/agentmarshal/extension_trust.py",
      "src/agentmarshal/process_log.py",
      "openspec/specs/extension-stages/spec.md",
      "archived extension-stage-run change artifacts",
      "archived extension-stage-run-fresh-copy change artifacts",
      "tests/test_stages.py"
    ],
    "not_run": [
      {
        "what": "Full repository CI sequence",
        "why": "The coordinator supplied its successful result for the exact reviewed commit; the provided snapshot is read-only and has no Git metadata."
      }
    ]
  },
  "evidence": {
    "CR211-MATERIALIZE-VALUEERROR": "src/agentmarshal/stages.py:280 and src/agentmarshal/stages.py:344; direct probe output: ValueError: embedded null byte",
    "CR211-PATH-OVERRIDE": "src/agentmarshal/stages.py:401 and openspec/specs/extension-stages/spec.md:150; direct probe output: /caller/bin"
  }
}
AGENTMARSHAL_VERDICT_END
