"""Tests for the onboarding health check command."""

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.doctor import run_doctor


def write_project_file(repo: Path, content: str) -> None:
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text(content, encoding="utf-8")


def init_git_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)


def test_doctor_passes_in_initialized_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 1}\n')
    monkeypatch.chdir(repo)

    assert main(["doctor"]) == 0

    output = capsys.readouterr().out
    assert output.count("OK:") == 4
    assert "Summary: all 4 checks passed" in output


def test_doctor_reports_outside_git_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    assert main(["doctor"]) == 1

    output = capsys.readouterr().out
    assert "FAIL: git repository" in output
    assert "FAIL: project initialized" in output


def test_doctor_reports_missing_project_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    monkeypatch.chdir(repo)

    assert main(["doctor"]) == 1

    assert "FAIL: project initialized" in capsys.readouterr().out


def test_doctor_reports_unknown_project_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 2}\n')
    monkeypatch.chdir(repo)

    assert main(["doctor"]) == 1

    assert "FAIL: project schema" in capsys.readouterr().out


def test_doctor_reports_malformed_project_file_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, "not json\n")
    monkeypatch.chdir(repo)

    assert main(["doctor"]) == 1

    output = capsys.readouterr()
    assert "FAIL: project schema" in output.out
    assert "Traceback" not in output.err


def test_doctor_reports_missing_git_executable(tmp_path: Path) -> None:
    results = run_doctor(tmp_path, resolver=lambda _name: None)

    git_result = results[0]
    assert not git_result.ok
    assert git_result.name == "git"
