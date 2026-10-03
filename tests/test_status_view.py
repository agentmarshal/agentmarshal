"""Pin the per-task ``status`` view's byte-exact output (CR-149).

The view is about to move from ``agentmarshal.cli`` to
``agentmarshal.journal.status_view`` behind a renderer registry. This test
records every record type the view has a dedicated line for — review,
acceptance, completed, finding, abandoned, reopened and amendment — plus
``opened`` and ``session``, which render with the generic id, type and time
line, and pins the full ``agentmarshal status <task>`` output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_abandoned_record,
    create_acceptance_record,
    create_amendment_record,
    create_completed_record,
    create_finding_record,
    create_opened_record,
    create_reopened_record,
    create_review_record,
    create_session_record,
    write_record,
)

_FINDING_ID = "00000000000000000000000003"
#: A second finding the first review carries in ``advisory_findings``; the
#: ``completed`` record that binds to it pins the ``completed_finding`` line.
_ADVISORY_FINDING_ID = "00000000000000000000000012"

_CONTRACT = """\
+++
schema = 1
id = "CR-001"
title = "Pinning task"
scope = ["src/", "tests/"]
acceptance = []
+++

# CR-001: Pinning task
"""


def _commit_file(repo: Path, name: str, content: str) -> str:
    (repo / name).write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", name], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            name,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_status_task_detail_output_is_pinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value without refused characters prints as it is.

    Byte-exact output is the pin: with escaping on display (ADR-0015
    decision 5) a record carrying no refused character renders identically.
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

    commit = _commit_file(repo, "tracked.py", "value = 1\n")
    journal = repo / ".agentmarshal" / "journal"
    task_directory = journal / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(_CONTRACT, encoding="utf-8")

    records: list[tuple[str, dict[str, object]]] = [
        ("00000000000000000000000001", create_opened_record("CR-001", "1.0")),
        (
            "00000000000000000000000002",
            create_review_record(
                "CR-001",
                "1.0",
                commit,
                "changes_required",
                "reviewer",
                "vendor",
                "model",
                "rev@example.invalid",
                ["F-1", "F-2"],
                advisory_findings=[_ADVISORY_FINDING_ID],
                artifacts=[{"ref": "review.md", "hash": "b" * 64}],
            ),
        ),
        (
            _FINDING_ID,
            create_finding_record(
                "CR-001",
                "1.0",
                "research notes",
                [
                    {"ref": "notes.md", "hash": "c" * 64},
                    {"ref": "log.txt", "hash": "d" * 64},
                ],
            ),
        ),
        (
            "00000000000000000000000004",
            create_review_record(
                "CR-001",
                "1.0",
                None,
                "approved",
                "reviewer",
                "vendor",
                "model",
                "rev@example.invalid",
                [],
                reviewed_finding=_FINDING_ID,
            ),
        ),
        (
            "00000000000000000000000005",
            create_acceptance_record(
                "CR-001",
                "1.0",
                None,
                "op-finding",
                ["F-1"],
                "finding accepted",
                accepted_finding=_FINDING_ID,
            ),
        ),
        (
            "00000000000000000000000006",
            create_acceptance_record(
                "CR-001",
                "1.0",
                commit,
                "test@example.invalid",
                ["F-1", "F-2"],
                "self override",
            ),
        ),
        (
            "00000000000000000000000007",
            create_acceptance_record(
                "CR-001",
                "1.0",
                "a" * 40,
                "op-unchecked",
                ["F-3"],
                "unchecked override",
            ),
        ),
        (
            "00000000000000000000000008",
            create_amendment_record("CR-001", "1.0", "scope clarified"),
        ),
        (
            "00000000000000000000000009",
            create_session_record(
                "CR-001",
                "1.0",
                "implementer",
                "tester",
                "implementation",
                "done",
                1,
                2,
                3,
            ),
        ),
        (
            "00000000000000000000000010",
            create_completed_record("CR-001", "1.0", commit),
        ),
        (
            "00000000000000000000000011",
            create_reopened_record("CR-001", "1.0", "regression found"),
        ),
        (
            _ADVISORY_FINDING_ID,
            create_finding_record(
                "CR-001",
                "1.0",
                "advisory note",
                [{"ref": "note.md", "hash": "e" * 64}],
            ),
        ),
        (
            "00000000000000000000000013",
            create_completed_record(
                "CR-001", "1.0", None, completed_finding=_ADVISORY_FINDING_ID
            ),
        ),
        (
            "00000000000000000000000014",
            create_reopened_record("CR-001", "1.0", "verification failed"),
        ),
        (
            "00000000000000000000000015",
            create_abandoned_record("CR-001", "1.0", "superseded"),
        ),
        (
            "00000000000000000000000016",
            create_session_record(
                "CR-001",
                "1.0",
                "implementer",
                "tester",
                "implementation",
                "done",
                4,
                5,
                6,
            ),
        ),
    ]
    for index, (record_id, record) in enumerate(records, start=1):
        record["created_at"] = f"2026-01-{index:02d}T00:00:00Z"
        write_record(journal, "CR-001", record, record_id=record_id)

    assert main(["status", "CR-001"]) == 0
    assert capsys.readouterr().out == (
        "ID: CR-001\n"
        "Status: abandoned\n"
        "Title: Pinning task\n"
        "Acceptance: accepted over findings by op-finding "
        "(finding 00000000000000000000000003)\n"
        "Acceptance: accepted over findings by test@example.invalid "
        "(self-accepted: accepting party is a declared author or committer)\n"
        "Acceptance: accepted over findings by op-unchecked "
        "(self-acceptance not checked: git cannot read aaaaaaa here)\n"
        "Scope:\n"
        "- src/\n"
        "- tests/\n"
        "Records:\n"
        "- 00000000000000000000000001 opened 2026-01-01T00:00:00Z\n"
        "- 00000000000000000000000002 review 2026-01-02T00:00:00Z "
        f"reviewed_commit={commit[:7]} verdict=changes_required "
        "findings=2 advisory=1 artifacts=1\n"
        "- 00000000000000000000000003 finding 2026-01-03T00:00:00Z "
        "summary=research notes artifacts=2\n"
        "- 00000000000000000000000004 review 2026-01-04T00:00:00Z "
        "reviewed_finding=00000000000000000000000003 "
        "verdict=approved findings=0 advisory=0\n"
        "- 00000000000000000000000005 acceptance 2026-01-05T00:00:00Z "
        "accepted_finding=00000000000000000000000003 "
        "accepted_by=op-finding findings=F-1 reason=finding accepted\n"
        "- 00000000000000000000000006 acceptance 2026-01-06T00:00:00Z "
        f"accepted_commit={commit[:7]} accepted_by=test@example.invalid "
        "findings=F-1,F-2 reason=self override self-accepted\n"
        "- 00000000000000000000000007 acceptance 2026-01-07T00:00:00Z "
        "accepted_commit=aaaaaaa accepted_by=op-unchecked "
        "findings=F-3 reason=unchecked override self-acceptance-unchecked\n"
        "- 00000000000000000000000008 amendment 2026-01-08T00:00:00Z "
        "reason=scope clarified\n"
        "- 00000000000000000000000009 session 2026-01-09T00:00:00Z\n"
        "- 00000000000000000000000010 completed 2026-01-10T00:00:00Z "
        f"completed_commit={commit[:7]}\n"
        "- 00000000000000000000000011 reopened 2026-01-11T00:00:00Z "
        "reason=regression found\n"
        "- 00000000000000000000000012 finding 2026-01-12T00:00:00Z "
        "summary=advisory note artifacts=1\n"
        "- 00000000000000000000000013 completed 2026-01-13T00:00:00Z "
        f"completed_finding={_ADVISORY_FINDING_ID}\n"
        "- 00000000000000000000000014 reopened 2026-01-14T00:00:00Z "
        "reason=verification failed\n"
        "- 00000000000000000000000015 abandoned 2026-01-15T00:00:00Z "
        "reason=superseded\n"
        "- 00000000000000000000000016 session 2026-01-16T00:00:00Z\n"
    )
