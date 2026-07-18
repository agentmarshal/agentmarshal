"""Smoke tests for the initial package surface."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import agentmarshal
from agentmarshal.cli import main
from agentmarshal.project import find_project_root, read_project_file


def run_git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    run_git("init", "--quiet", cwd=repo)


def commit_empty(repo: Path) -> None:
    run_git(
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "--allow-empty",
        "--quiet",
        "-m",
        "init",
        cwd=repo,
    )


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
    init_git_repo(repo)
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
    init_git_repo(repo)
    subdir = repo / "a" / "b"
    subdir.mkdir(parents=True)
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
    init_git_repo(repo)
    subdir = repo / "nested"
    subdir.mkdir(parents=True)
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


@pytest.mark.parametrize("marker_kind", ["file", "incomplete_directory"])
def test_init_rejects_invalid_git_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    marker_kind: str,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    git_path = workspace / ".git"
    if marker_kind == "file":
        git_path.write_text("not a gitdir\n", encoding="utf-8")
    else:
        git_path.mkdir()
        (git_path / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    monkeypatch.chdir(workspace)

    assert main(["init"]) == 1

    assert "inside a git repository" in capsys.readouterr().err
    assert not (workspace / ".agentmarshal").exists()


def test_init_in_separate_git_dir_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        [
            "git",
            "init",
            "--quiet",
            "--separate-git-dir",
            str(tmp_path / "meta.git"),
            str(repo),
        ],
        check=True,
        capture_output=True,
    )
    monkeypatch.chdir(repo)

    assert main(["init"]) == 0

    assert (repo / ".agentmarshal" / "project.json").is_file()


def test_init_in_linked_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    commit_empty(repo)
    worktree = tmp_path / "worktree"
    run_git("worktree", "add", "--quiet", str(worktree), cwd=repo)
    monkeypatch.chdir(worktree)

    assert main(["init"]) == 0

    assert (worktree / ".agentmarshal" / "project.json").is_file()
    assert not (repo / ".agentmarshal").exists()


def test_init_in_submodule_working_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    child = tmp_path / "child"
    init_git_repo(child)
    commit_empty(child)
    parent = tmp_path / "parent"
    init_git_repo(parent)
    commit_empty(parent)
    run_git(
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "--quiet",
        str(child),
        "sub",
        cwd=parent,
    )
    submodule = parent / "sub"
    monkeypatch.chdir(submodule)

    assert main(["init"]) == 0

    assert (submodule / ".agentmarshal" / "project.json").is_file()
    assert not (parent / ".agentmarshal").exists()


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
