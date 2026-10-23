"""The status view's line for the session behind the reviewed commit (CR-208).

Proposal 036's read side: `status` prints one line for the commit the
task's latest review judged — the implementer session whose `commit`
equals it — its id, `actor`, `outcome` and `report_ready` when carried,
saying plainly when the run did not end `implemented`, and counting the
earlier naming sessions. No review, a review bound to a finding, or no
implementer session naming the commit prints exactly what the view
prints without the line — a candidate produced by a runner that wrote
no session is shown as before.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmarshal.journal.contracts import ContractHeader
from agentmarshal.journal.status import TaskStatus
from agentmarshal.journal.status_view import print_task_detail

_COMMIT = "a" * 40
_OTHER_COMMIT = "b" * 40


def _contract(task_id: str = "CR-001") -> ContractHeader:
    return ContractHeader(
        schema=1, id=task_id, title="Task", scope=("src/",), acceptance=()
    )


def _opened() -> dict[str, object]:
    return {"id": "r-open", "record_type": "opened", "created_at": "t0"}


def _review(
    review_id: str, verdict: str = "approved", **extra: object
) -> dict[str, object]:
    record: dict[str, object] = {
        "id": review_id,
        "record_type": "review",
        "created_at": "t1",
        "reviewed_commit": _COMMIT,
        "verdict": verdict,
        "findings": [],
        "advisory_findings": [],
    }
    record.update(extra)
    if "reviewed_finding" in extra:
        # A review binds exactly one of commit and finding.
        del record["reviewed_commit"]
    return record


def _session(session_id: str, **extra: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": session_id,
        "record_type": "session",
        "created_at": "t2",
        "role": "implementer",
        "actor": "impl-agent",
        "activity": "implementation",
        "outcome": "implemented",
        "commit": _COMMIT,
    }
    record.update(extra)
    return record


def _task(*records: dict[str, object], state: str = "open") -> TaskStatus:
    return TaskStatus(
        task_id="CR-001",
        contract=_contract(),
        records=records,
        state=state,
    )


def _project(tmp_path: Path) -> Path:
    """A journal root under a project carrying a readable ``project.json``."""

    journal_root = tmp_path / "project" / ".agentmarshal" / "journal"
    journal_root.mkdir(parents=True)
    (journal_root.parent / "project.json").write_text("{}\n", encoding="utf-8")
    return journal_root


def test_the_producing_implementer_session_is_named(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the producing implementer session is named.

    The task's latest review judged a commit an implementer session's
    `commit` names — the line names the session's id, actor and
    outcome. A session carrying no `report_ready` shows none.
    """

    task = _task(_opened(), _review("r-review"), _session("r-session"))

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert (
        f"Reviewed commit {_COMMIT[:7]}: implementer session r-session "
        "actor=impl-agent outcome=implemented\n"
    ) in out


def test_report_ready_prints_when_the_record_carries_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: report_ready prints when the record carries it.

    `report_ready` is shown as the JSON boolean the record carries —
    `false` included, a value carried rather than a field omitted — and
    a session carrying none shows none.
    """

    task = _task(
        _opened(),
        _review("r-review"),
        _session("r-session", report_ready=False),
    )

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert "outcome=implemented report_ready=false\n" in out


def test_an_outcome_other_than_implemented_is_said_plainly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an outcome other than implemented is said plainly.

    The producing session ended `provider-limit` — the review approved
    a candidate its run did not finish, proposal 036's case, and the
    line says the run did not end `implemented`.
    """

    task = _task(
        _opened(),
        _review("r-review"),
        _session("r-session", outcome="provider-limit", report_ready=True),
    )

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert (
        "outcome=provider-limit report_ready=true (did not end 'implemented')\n" in out
    )


def test_the_latest_of_several_naming_sessions_is_shown_and_the_earlier_counted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the latest of several naming sessions is shown and the earlier counted.

    Three implementer sessions name the reviewed commit — a rerun after
    an interruption produces the same head. The line shows the last in
    stored order and counts the two earlier ones.
    """

    task = _task(
        _opened(),
        _session("s-first", actor="impl-a", outcome="stalled"),
        _session("s-second", actor="impl-b", outcome="failed"),
        _review("r-review"),
        _session("s-third", actor="impl-c", outcome="implemented"),
    )

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert (
        "implementer session s-third actor=impl-c outcome=implemented "
        "(+2 earlier implementer sessions)\n" in out
    )
    # The earlier two show only on their own generic record lines —
    # the producing line names the latest alone.
    assert out.count("implementer session ") == 1


def test_a_review_bound_to_a_finding_produces_no_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a review bound to a finding produces no line.

    The task's latest review binds a finding — it judged no commit, so
    there is no reviewed commit to name a producer for, even with an
    implementer session standing by and an earlier review having judged
    the commit: the last review record wins.
    """

    task = _task(
        _opened(),
        _review("r-earlier", "changes_required", findings=["F-1"]),
        _review(
            "r-review",
            reviewed_finding="F-1",
            findings=["F-1"],
        ),
        _session("r-session"),
    )

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert "Reviewed commit" not in out


def test_a_task_holding_no_review_produces_no_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task holding no review produces no line.

    Sessions exist, but no review has judged a commit — nothing to name
    a producer for.
    """

    task = _task(_opened(), _session("r-session"))

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert "Reviewed commit" not in out


def test_a_candidate_no_implementer_session_names_prints_as_before(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a candidate no implementer session names prints as before.

    The byte-for-byte pin (proposal 036's disposition): a candidate
    produced by a runner that wrote no session — the review judged a
    commit no implementer session names, whether the session recorded a
    different commit or none — shows exactly the detail view it printed
    before the line existed.
    """

    without_commit = _session("s-nocommit", outcome="failed")
    del without_commit["commit"]
    task = _task(
        _opened(),
        _session("r-session", commit=_OTHER_COMMIT, outcome="failed"),
        without_commit,
        _review("r-review", "changes_required", findings=["F-1"]),
    )

    journal_root = _project(tmp_path)
    print_task_detail(tmp_path / "project", task, journal_root)

    assert capsys.readouterr().out == (
        "ID: CR-001\n"
        "Status: open\n"
        "Title: Task\n"
        "Scope:\n"
        "- src/\n"
        "Records:\n"
        "- r-open opened t0\n"
        "- r-session session t2\n"
        "- s-nocommit session t2\n"
        "- r-review review t1 reviewed_commit=aaaaaaa "
        "verdict=changes_required findings=1 advisory=0\n"
        "No agreement with the contract is recorded\n"
        "changes_required verdicts for CR-001: 1 (threshold 3)\n"
    )


def test_a_session_of_another_role_naming_the_commit_produces_no_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a session of another role naming the commit produces no line.

    A reviewer's session and a coordination session name the reviewed
    commit — neither is an implementer session, so the candidate reads
    as produced by a runner that wrote no session.
    """

    task = _task(
        _opened(),
        _session("s-reviewer", role="reviewer", activity="review"),
        _session("s-coord", role="coordinator", activity="coordination"),
        _review("r-review"),
    )

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert "Reviewed commit" not in out


def test_todays_lines_print_unchanged_and_the_session_line_follows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: today's lines print unchanged and the session line follows.

    A task whose view carries the agreement and count lines: every line
    printed before this change stands unchanged, and the session line
    prints after them all.
    """

    task = _task(
        _opened(),
        _session("r-session"),
        _review("r-review", "changes_required", findings=["F-1"]),
    )

    journal_root = _project(tmp_path)
    print_task_detail(tmp_path / "project", task, journal_root)

    assert capsys.readouterr().out == (
        "ID: CR-001\n"
        "Status: open\n"
        "Title: Task\n"
        "Scope:\n"
        "- src/\n"
        "Records:\n"
        "- r-open opened t0\n"
        "- r-session session t2\n"
        "- r-review review t1 reviewed_commit=aaaaaaa "
        "verdict=changes_required findings=1 advisory=0\n"
        "No agreement with the contract is recorded\n"
        "changes_required verdicts for CR-001: 1 (threshold 3)\n"
        f"Reviewed commit {_COMMIT[:7]}: implementer session r-session "
        "actor=impl-agent outcome=implemented\n"
    )


def test_a_record_value_on_the_session_line_is_escaped_on_display(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a record value on the session line is escaped on display.

    Built in memory, as in the escaping pin — an actor and an outcome
    carrying characters the forgeable-text rule refuses print escaped
    on the session line; they can neither add a line nor reorder one.
    """

    task = _task(
        _opened(),
        _review("r-review"),
        _session("r-session", actor="im\npl", outcome="imple\u202emented"),
    )

    print_task_detail(tmp_path, task, tmp_path)

    out = capsys.readouterr().out
    assert (
        "implementer session r-session actor=im\\npl "
        "outcome=imple\\u202emented (did not end 'implemented')\n" in out
    )
    assert "im\npl" not in out
