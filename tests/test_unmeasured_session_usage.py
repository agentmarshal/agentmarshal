"""An unmeasured session reads as unmeasured in ``status`` and ``report``.

``record-session`` without token flags writes ``0/0/0`` — zeros
indistinguishable from a free run, the only trace that nothing was
measured being a missing ``usage`` block (digest 044's finding). One
predicate — every token count zero and no ``usage`` block — reads such a
session as unmeasured: ``status`` shows its tokens as ``unmeasured``, and
``report`` leaves it out of every token and cost sum, naming the count
wherever such a sum prints. A session with a ``usage`` block, or any
non-zero token count, reads exactly as today. Every scenario the delta
spec names is exercised by one test whose docstring names it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import create_session_record, write_record
from agentmarshal.journal.report import _is_unmeasured

_DECLARATION = (
    "A check record is the observer's declaration of what the pipeline found "
    "on the commit, not proof of it."
)


def _initialize_repo(repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    # A local identity, so `recorded_by` resolves where a record needs it —
    # CI runs with no global one.
    for arguments in (
        ("config", "user.name", "Recorder"),
        ("config", "user.email", "recorder@test.invalid"),
    ):
        subprocess.run(["git", *arguments], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo / ".agentmarshal" / "journal"


def _open(journal: Path, task_id: str) -> None:
    """Open a task; the report tests need the record, not a known time."""

    assert main(["open", "--title", f"Task {task_id}"]) == 0
    assert list((journal / "tasks" / task_id / "records").glob("*-opened.json"))


def _session(
    task_id: str,
    *,
    tokens: tuple[int, int, int] = (0, 0, 0),
    usage: tuple[str, str] | None = None,
    cost: dict[str, str] | None = None,
) -> dict[str, object]:
    return create_session_record(
        task_id,
        "1.0",
        "implementer",
        "vendor/model",
        "implementation",
        "implemented",
        *tokens,
        usage_provider=None if usage is None else usage[0],
        usage_method=None if usage is None else usage[1],
        cost=cost,
    )


def _status_session_lines(output: str) -> list[str]:
    return [
        line
        for line in output.splitlines()
        if line.startswith("- ") and " session " in line
    ]


def test_zero_tokens_and_no_usage_is_unmeasured() -> None:
    """Scenario: zero tokens and no usage is unmeasured."""

    assert _is_unmeasured(_session("CR-001"))


def test_a_session_with_a_usage_block_reads_as_today() -> None:
    """Scenario: a session with a usage block reads as today."""

    # A `usage` block marks the session measured even at zero tokens —
    # the zeros are a recorded measurement, not a missing one.
    for method in ("measured", "reported"):
        assert not _is_unmeasured(
            _session("CR-001", usage=("example-provider", method))
        )


def test_a_session_with_a_non_zero_token_reads_as_today() -> None:
    """Scenario: a session with a non-zero token reads as today."""

    assert not _is_unmeasured(_session("CR-001", tokens=(1, 0, 0)))
    assert not _is_unmeasured(_session("CR-001", tokens=(0, 0, 7)))


def test_an_unmeasured_sessions_tokens_show_as_unmeasured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unmeasured session's tokens show as unmeasured."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    session = _session("CR-001")
    session["created_at"] = "2026-01-01T00:00:00Z"
    path = write_record(journal, "CR-001", session)
    capsys.readouterr()

    assert main(["status", "CR-001"]) == 0
    record_id = path.name.removesuffix("-session.json")
    assert _status_session_lines(capsys.readouterr().out) == [
        f"- {record_id} session 2026-01-01T00:00:00Z tokens=unmeasured"
    ]


def test_a_measured_sessions_line_is_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a measured session's line is unchanged."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    sessions = [
        _session("CR-001", tokens=(4, 5, 6), usage=("example-provider", "reported")),
        _session("CR-001", tokens=(0, 1, 0)),
    ]
    paths = [write_record(journal, "CR-001", session) for session in sessions]
    capsys.readouterr()

    assert main(["status", "CR-001"]) == 0
    assert _status_session_lines(capsys.readouterr().out) == [
        f"- {path.name.removesuffix('-session.json')} session {session['created_at']}"
        for path, session in zip(paths, sessions, strict=True)
    ]


def test_the_task_line_names_the_unmeasured_sessions_it_left_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the task line names the unmeasured sessions it left out."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    write_record(journal, "CR-001", _session("CR-001"))
    write_record(journal, "CR-001", _session("CR-001"))
    write_record(journal, "CR-001", _session("CR-001", tokens=(5, 0, 0)))
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("CR-001\t")
    assert "\ttokens=5" in lines[0]
    assert lines[0].endswith("\tunmeasured=2")


def test_the_summary_names_the_unmeasured_sessions_it_left_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the summary names the unmeasured sessions it left out."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    write_record(journal, "CR-001", _session("CR-001"))
    write_record(journal, "CR-002", _session("CR-002"))
    write_record(journal, "CR-002", _session("CR-002", tokens=(3, 2, 0)))
    capsys.readouterr()

    assert main(["report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    summary = next(line for line in lines if line.startswith("Summary\t"))
    assert "\ttokens=5" in summary
    assert summary.endswith("\tunmeasured=2")


def test_a_task_holding_only_unmeasured_sessions_prints_no_cost_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task holding only unmeasured sessions prints no cost lines."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    write_record(journal, "CR-001", _session("CR-001"))
    write_record(
        journal,
        "CR-001",
        _session(
            "CR-001",
            cost={"amount": "1.00", "currency": "USD", "source": "reported"},
        ),
    )
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert not any(line.startswith("Cost\t") for line in lines)
    assert lines[0].endswith("\tunmeasured=2")


def test_an_unmeasured_sessions_cost_is_left_out_of_the_sums(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unmeasured session's cost is left out of the sums."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    write_record(
        journal,
        "CR-001",
        _session(
            "CR-001",
            cost={"amount": "9.99", "currency": "USD", "source": "reported"},
        ),
    )
    write_record(
        journal,
        "CR-001",
        _session(
            "CR-001",
            tokens=(1, 1, 1),
            cost={"amount": "0.01", "currency": "USD", "source": "reported"},
        ),
    )
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Cost\tUSD\treported=0.01\tunmeasured=1" in lines
    assert not any("9.99" in line for line in lines)


def test_every_cost_line_names_the_sessions_left_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every Cost line names the sessions left out."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    write_record(journal, "CR-001", _session("CR-001"))
    write_record(journal, "CR-001", _session("CR-001", tokens=(2, 0, 0)))
    write_record(
        journal,
        "CR-001",
        _session(
            "CR-001",
            tokens=(1, 1, 1),
            cost={"amount": "1.00", "currency": "USD", "source": "reported"},
        ),
    )
    write_record(
        journal,
        "CR-001",
        _session(
            "CR-001",
            tokens=(1, 1, 1),
            cost={"amount": "2.00", "currency": "EUR", "source": "estimated"},
        ),
    )
    capsys.readouterr()

    assert main(["report", "--task", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [line for line in lines if line.startswith("Cost\t")] == [
        "Cost\tEUR\testimated=2.00\tunmeasured=1",
        "Cost\tUSD\treported=1.00\tunmeasured=1",
        "Cost\tsessions_without_cost=1\tunmeasured=1",
    ]


def test_the_aggregate_leaves_unmeasured_sessions_out_and_names_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the aggregate leaves unmeasured sessions out and names them."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    _open(journal, "CR-002")
    write_record(journal, "CR-001", _session("CR-001"))
    write_record(journal, "CR-002", _session("CR-002"))
    write_record(
        journal,
        "CR-002",
        _session(
            "CR-002",
            tokens=(1, 1, 1),
            cost={"amount": "1.00", "currency": "USD", "source": "reported"},
        ),
    )
    capsys.readouterr()

    assert main(["report"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "Cost\tUSD\treported=1.00\tunmeasured=2" in lines
    assert "Cost\tsessions_without_cost=0\tunmeasured=2" in lines


def test_with_no_unmeasured_session_nothing_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: with no unmeasured session nothing changes."""

    repo = tmp_path / "repo"
    journal = _initialize_repo(repo, monkeypatch)
    _open(journal, "CR-001")
    write_record(
        journal,
        "CR-001",
        _session("CR-001", tokens=(4, 0, 0), usage=("example-provider", "measured")),
    )
    capsys.readouterr()

    assert main(["status", "CR-001"]) == 0
    assert "unmeasured" not in capsys.readouterr().out

    assert main(["report"]) == 0
    report_lines = capsys.readouterr().out.splitlines()
    assert not any("unmeasured" in line for line in report_lines)
    assert report_lines[-2:] == [
        "Checks\trejected_commits=0",
        _DECLARATION,
    ]
