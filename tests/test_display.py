"""Escaping on display (CR-155).

ADR-0015 decision 5: what the forgeable-text rule refuses at write is escaped
where the tool displays it. A record is checked at read time by the rules of
its own schema, so the hostile records below are built in memory — today's
read rules would refuse them on disk — which is exactly the shape an older
journal, or a record written around the writer, can hand the renderers.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.contracts import ContractHeader
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.records import (
    create_opened_record,
    forges_rendered_text,
    write_record,
)
from agentmarshal.journal.report import (
    JournalReport,
    _task_report,
    format_report,
)
from agentmarshal.journal.status import TaskStatus
from agentmarshal.journal.status_view import print_task_detail


def test_what_the_write_refuses_the_display_escapes() -> None:
    """Scenario: what the write refuses, the display escapes.

    The cases are derived from ``forges_rendered_text`` itself — the same
    predicate the writer consults — so the test fails the day the rule and
    the escape disagree, in either direction.
    """

    # One pass over the whole plane, character by character: a failure names
    # the codepoint, and comparing per character pins the accepted ones too —
    # each prints as it is.
    for codepoint in range(0x110000):
        character = chr(codepoint)
        if not forges_rendered_text(character):
            assert escape_for_display(character) == character, f"U+{codepoint:04X}"
            continue
        if character == "\n":
            escape = "\\n"
        elif character == "\r":
            escape = "\\r"
        elif character == "\t":
            escape = "\\t"
        elif codepoint <= 0xFFFF:
            escape = f"\\u{codepoint:04x}"
        else:
            escape = f"\\U{codepoint:08x}"
        assert escape_for_display(character) == escape, f"U+{codepoint:04X}"


def test_a_refusal_past_the_bmp_escapes_as_UXXXXXXXX(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario: what the write refuses, the display escapes.

    Today's rule refuses nothing past the Basic Multilingual Plane, so the
    ``\\UXXXXXXXX`` form is unreachable through the real predicate. The
    escape consults the predicate per character, so a rule stood in that
    refuses U+1F600 demonstrates the form for the day the rule grows to
    reach it — the escape follows whatever the predicate refuses.
    """

    def refuses_an_astral_character(value: str) -> bool:
        return any(ord(character) > 0xFFFF for character in value)

    monkeypatch.setattr(
        "agentmarshal.journal.display.forges_rendered_text",
        refuses_an_astral_character,
    )

    assert escape_for_display("x\U0001f600y") == "x\\U0001f600y"


def test_a_refused_character_prints_escaped_in_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a refused character prints escaped in status.

    The records are built in memory — today's read rules would refuse them
    on disk — because under ADR-0015 a later rule does not reach an older
    schema's records, so this is the shape the view must survive: a newline
    and a right-to-left override in every free-text field a renderer prints,
    each shown escaped on the record's one line.
    """

    task = TaskStatus(
        task_id="CR-001",
        contract=ContractHeader(
            schema=1,
            id="CR-001",
            title="Pinning\u202e task",
            scope=("src/\u202ex",),
            acceptance=(),
        ),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            {
                "id": "r-review",
                "record_type": "review",
                "created_at": "t1",
                "reviewed_finding": "F\u202e1",
                "verdict": "approved\nforged",
                "findings": [],
                "advisory_findings": ["A\u202e1"],
            },
            {
                "id": "r-acceptance",
                "record_type": "acceptance",
                "created_at": "t2",
                "accepted_finding": "F\u202e2",
                "accepted_by": "op\u202eerator",
                "findings": ["F-1", "F\n2"],
                "reason": "looks fine\ngate: passed",
            },
            {
                "id": "r-finding",
                "record_type": "finding",
                "created_at": "t3",
                "summary": "one\ntwo\u202e",
                "artifacts": [{"ref": "x", "hash": "0" * 64}],
            },
            {
                "id": "r-completed",
                "record_type": "completed",
                "created_at": "t4",
                "completed_finding": "F\u202e3",
            },
            {
                "id": "r-reopened",
                "record_type": "reopened",
                "created_at": "t5",
                "reason": "back\n\u202e",
            },
            {"id": "r-session", "record_type": "session", "created_at": "t6"},
        ),
        state="open",
    )

    print_task_detail(tmp_path, task)

    assert capsys.readouterr().out == (
        "ID: CR-001\n"
        "Status: open\n"
        "Title: Pinning\\u202e task\n"
        "Acceptance: accepted over findings by op\\u202eerator "
        "(finding F\\u202e2)\n"
        "Scope:\n"
        "- src/\\u202ex\n"
        "Records:\n"
        "- r-open opened t0\n"
        "- r-review review t1 reviewed_finding=F\\u202e1 "
        "verdict=approved\\nforged findings=0 advisory=1\n"
        "- r-acceptance acceptance t2 accepted_finding=F\\u202e2 "
        "accepted_by=op\\u202eerator findings=F-1,F\\n2 "
        "reason=looks fine\\ngate: passed\n"
        "- r-finding finding t3 summary=one\\ntwo\\u202e artifacts=1\n"
        "- r-completed completed t4 completed_finding=F\\u202e3\n"
        "- r-reopened reopened t5 reason=back\\n\\u202e\n"
        "- r-session session t6\n"
    )


def test_status_task_list_escapes_contract_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a refused character prints escaped in status (the task list).

    The contract header leaves `title` unchecked (`contracts.py`), so a TOML
    escape is how a contract file carries a character the rule refuses: the
    header is split with `str.splitlines()`, which is why the title below
    carries the bidirectional override and not a raw newline. The list
    form's stdout pin is also the ``status`` paths change's scenario —
    stdout stays what the documentation promises.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "tester")

    journal = repo / ".agentmarshal" / "journal"
    task_directory = journal / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        "+++\n"
        "schema = 1\n"
        'id = "CR-001"\n'
        'title = "Task\\u202e one"\n'
        'scope = ["src/"]\n'
        "acceptance = []\n"
        "+++\n\n# CR-001\n",
        encoding="utf-8",
    )
    write_record(journal, "CR-001", create_opened_record("CR-001", "1.0"))

    assert main(["status"]) == 0

    captured = capsys.readouterr()
    assert captured.out == "CR-001\topen\tTask\\u202e one\n"
    # CR-162: the paths print once on stderr, after the placement line —
    # stdout keeps the pin (ADR-0014 decision 13).
    assert captured.err == (
        "Placement: embedded\n"
        f"journal: {repo.resolve() / '.agentmarshal' / 'journal'}\n"
        f"process log: {repo.resolve() / '.git' / 'agentmarshal' / 'log'}\n"
        f"local state: {repo.resolve() / '.git' / 'agentmarshal'}\n"
    )


def test_a_refused_character_prints_escaped_in_report() -> None:
    """Scenario: a refused character prints escaped in report.

    The session record's usage method is built in memory — today's read rules
    would refuse it on disk — so `format_report` is handed the value an older
    journal can carry.
    """

    status = TaskStatus(
        task_id="CR-009\nforged",
        contract=ContractHeader(
            schema=1, id="CR-009", title="Task", scope=("src/",), acceptance=()
        ),
        records=(
            {
                "record_type": "session",
                "tokens": {"input": 4},
                "usage": {"method": "measured\u202e forged"},
            },
        ),
        state="open",
    )
    report = JournalReport(
        tasks=(_task_report(status),),
        review_cycles=0,
        tokens=4,
        usage_provenance="rep\u202eorted\nforged",
    )

    assert format_report(report) == (
        "CR-009\\nforged\topen\treviews=0\ttokens=4\tusage=measured\\u202e forged",
        "Summary\topen=1\treviews=0\ttokens=4\tusage=rep\\u202eorted\\nforged",
    )
