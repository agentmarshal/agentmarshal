"""Tests for implementer briefings."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.brief import build_brief
from agentmarshal.journal.contracts import JournalContractError


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert (
        main(
            [
                "open",
                "--title",
                "Brief task",
                "--scope",
                "src/app.py",
                "--scope",
                "tests/test_app.py",
            ]
        )
        == 0
    )
    return repo


def _contract(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"


def _write_contract(repo: Path) -> str:
    body = (
        "\n# CR-001: Brief task\n\n"
        "## Threat model and boundaries\n\n"
        "Keep <prompt-like> text exactly.\n\n"
        "## Non-Goals\n\n"
        "- Do not add another format.\n"
    )
    _contract(repo).write_text(
        "+++\n"
        "schema = 1\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        'scope = ["src/app.py", "tests/test_app.py"]\n'
        'acceptance = ["prints the body", "names every rule"]\n'
        "+++\n"
        f"{body}",
        encoding="utf-8",
    )
    return body


def test_brief_prints_complete_contract_and_governance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    body = _write_contract(repo)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.endswith(body)
    assert "Task id: CR-001" in captured.out
    assert "- src/app.py" in captured.out
    assert "- tests/test_app.py" in captured.out
    assert "- prints the body" in captured.out
    assert "- names every rule" in captured.out
    assert "only these paths may change" in captured.out
    assert "the journal is not the implementer's to edit" in captured.out
    assert "they are the definition of done" in captured.out


@pytest.mark.parametrize(("state", "reason"), [("abandoned", "superseded")])
def test_brief_refuses_a_task_that_is_not_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state: str,
    reason: str,
) -> None:
    _repo(tmp_path, monkeypatch)
    assert main(["abandon", "--task", "CR-001", "--reason", reason]) == 0
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert state in captured.err


def test_brief_refuses_unknown_task_and_names_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _repo(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-999"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unknown task id: CR-999" in captured.err


def test_malformed_contract_raises_contract_error_and_cli_reports_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _contract(repo).write_text("not a contract\n", encoding="utf-8")
    journal = repo / ".agentmarshal" / "journal"
    capsys.readouterr()

    with pytest.raises(JournalContractError):
        build_brief(journal, "CR-001")
    assert main(["brief", "--task", "CR-001"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "contract must start with a +++ header delimiter" in captured.err
