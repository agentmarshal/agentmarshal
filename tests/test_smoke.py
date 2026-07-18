"""Smoke tests for the initial package surface."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import agentmarshal
from agentmarshal.cli import main
from agentmarshal.project import find_project_root, read_project_file


def create_git_marker(repo: Path) -> None:
    git_dir = repo / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")


def test_version_is_declared() -> None:
    assert agentmarshal.__version__ == "0.1.0.dev0"


def test_console_version_prints_package_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "agentmarshal", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == f"{agentmarshal.__version__}\n"


def test_init_creates_project_file_at_git_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    create_git_marker(repo)
    monkeypatch.chdir(repo)

    assert main(["init"]) == 0

    project_file = repo / ".agentmarshal" / "project.json"
    raw_content = project_file.read_bytes()
    assert not raw_content.startswith(b"\xef\xbb\xbf")
    assert raw_content.endswith(b"\n")
    assert b"\r\n" not in raw_content
    assert json.loads(raw_content.decode("utf-8")) == {
        "framework": {"version": agentmarshal.__version__},
        "schema": 1,
    }
    assert capsys.readouterr().err == ""


def test_init_refuses_existing_project_from_subdirectory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    subdir = repo / "a" / "b"
    subdir.mkdir(parents=True)
    create_git_marker(repo)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    before = project_file.read_bytes()
    monkeypatch.chdir(subdir)

    assert main(["init"]) == 1

    output = capsys.readouterr()
    assert str(repo) in output.err
    assert "already initialized" in output.err
    assert project_file.read_bytes() == before


def test_init_from_subdirectory_writes_to_git_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    subdir = repo / "nested"
    subdir.mkdir(parents=True)
    create_git_marker(repo)
    monkeypatch.chdir(subdir)

    assert main(["init"]) == 0

    assert (repo / ".agentmarshal" / "project.json").is_file()
    assert not (subdir / ".agentmarshal").exists()


def test_init_outside_git_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    assert main(["init"]) == 1

    output = capsys.readouterr()
    assert "inside a git repository" in output.err
    assert not (workspace / ".agentmarshal").exists()


def test_project_discovery_through_cyrillic_directory(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    nested = repo / "задачи" / "inside"
    nested.mkdir(parents=True)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")

    assert find_project_root(nested) == repo


def test_read_project_file_accepts_utf8_bom(tmp_path: Path) -> None:
    project_file = tmp_path / "project.json"
    project_file.write_text('\ufeff{"schema": 1}\n', encoding="utf-8")

    assert read_project_file(project_file) == {"schema": 1}
