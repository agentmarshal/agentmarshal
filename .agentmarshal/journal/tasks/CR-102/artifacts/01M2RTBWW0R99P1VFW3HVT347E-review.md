I reviewed the diff statically. Note up front: I was not able to execute the test suite — the sandbox refused the `pytest` invocations — so everything below is from reading the code, not from a run.

**What holds up.** The guard is genuinely single-sourced: `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL` in `src/agentmarshal/journal/status.py:29` is read by both `project_status` and `load_task_for_record`, and a grep of the tree turns up no second list of admitted-after-terminal types. Every `write_record` call site that targets an existing task is now behind the helper: `submit_review.py:55`, `session.py:50`, `acceptance.py:34`, `complete.py:53/74/104`, and `cli.py:881/955/988/1012`; `open_task.py` creates a task and `migrate.py`/`backfill.py` are not lifecycle writers. Both launcher paths refuse at load time before any snapshot or reviewer process (`review.py:822` and `review.py:1002`, the latter ahead of `_resolve_commit`). `reopen` stays correct because `"reopened"` is exempted by the helper and `cli.py:990` still holds the `state != "done"` check that the projection also enforces. The `accept`/`amend`/`complete`/`abandon` message change from "has a terminal record" / "is not open" to the new combined wording keeps the substring `is not open (state: …)` that `tests/test_journal.py:1000` asserts.

Below are the advisory findings.

ADV-001 — `tests/test_review_launcher.py:925`: the docstring of `test_a_closed_task_is_refused_before_running` was changed from `"""Scenario: a closed task is refused."""` to the new record-lifecycle scenario name, but `openspec/specs/findings-review/spec.md:93` still carries a live `#### Scenario: a closed task is refused`, and a grep of `tests/` now finds no docstring naming it. The behaviour is still covered by that same test body; only the traceability label was reassigned away from a capability this change does not own.

ADV-002 — `tests/test_review_launcher.py:925` and `:955`: both closed-task launcher tests use a bare docstring, while the other 28 scenario-naming tests in that file use the `Scenario: ` prefix. The two new commit/finding launcher tests are now the only ones in the file that a grep for the convention's marker will miss.

ADV-003 — `src/agentmarshal/journal/status.py:105`: `load_task_for_record` accepts `record_type` as an unvalidated string and never checks it against `_RECORD_TYPE_STATES`, which sits eleven lines above the constant it does consult. A caller typo in the direction of `"session"` (say `"sessions"`) would silently start refusing the am-land cost step on completed tasks, and nothing but a test would catch it.

ADV-004 — `tests/test_journal.py`, `test_every_writing_command_refuses_a_closed_task`: the parametrization varies the command but not the terminal state — `_terminal_task` defaults to `completed`, so `accept`, `amend`, `finding`, `complete` and `abandon` are exercised only against `done`. Only `submit-review` gets both states, via the two dedicated scenario tests. The acceptance criterion reads "for each terminal state, every command…"; the change's own `tasks.md` 2.2/2.3 reads it as one test per command, so this is a reading gap rather than a defect, and the guard itself is state-agnostic.

ADV-005 — `openspec/specs/record-lifecycle/spec.md:44`: the requirement "The launcher refuses before it spends a reviewer run" is verbatim the name of an existing requirement at `openspec/specs/findings-review/spec.md:67`, and the new scenario restates a rule the older one already states for the finding path. The contract's scope did not permit editing `findings-review`, so this was unavoidable here, but the same normative rule now lives in two capabilities — the shape of drift this change's own `design.md` cites CR-100 and CR-101 for.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "65b664fe1d10d12ac240865795a629af4286f7d7",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-001", "ADV-002", "ADV-003", "ADV-004", "ADV-005"]
}
AGENTMARSHAL_VERDICT_END
