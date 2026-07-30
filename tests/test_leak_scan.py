"""Tests for the provider-neutral ``agentmarshal leak-scan`` command."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    base = _commit_all(repo, "base")
    return repo, base


def _add_file(repo: Path, path: str, content: str) -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _commit_all(repo, f"add {path}")


def test_leak_scan_flags_secret_in_added_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, base = _repo(tmp_path, monkeypatch)
    head = _add_file(repo, "secret.py", "key = 'AKIAIOSFODNN7EXAMPLE'\n")

    code = main(["leak-scan", "--base", base, "--commit", head])

    assert code == 1
    out = capsys.readouterr().out
    assert "aws-access-key-id" in out


def test_leak_scan_passes_clean_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, base = _repo(tmp_path, monkeypatch)
    head = _add_file(repo, "module.py", "def add(a, b):\n    return a + b\n")

    code = main(["leak-scan", "--base", base, "--commit", head])

    assert code == 0
    assert "no known leak signatures" in capsys.readouterr().out


def test_leak_scan_never_echoes_the_secret(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, base = _repo(tmp_path, monkeypatch)
    head = _add_file(repo, "secret.py", "key = 'AKIAIOSFODNN7EXAMPLE'\n")

    main(["leak-scan", "--base", base, "--commit", head])

    captured = capsys.readouterr()
    assert "AKIAIOSFODNN7EXAMPLE" not in captured.out
    assert "AKIAIOSFODNN7EXAMPLE" not in captured.err


def test_leak_scan_uses_configured_private_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, _ = _repo(tmp_path, monkeypatch)
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": ["internal.example.invalid"]}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # Markers are read from the base (merge-base) tree, so the config must be
    # committed on the base being scanned against.
    base = _commit_all(repo, "configure markers")
    head = _add_file(repo, "host.py", "HOST = 'internal.example.invalid'\n")

    code = main(["leak-scan", "--base", base, "--commit", head])

    assert code == 1
    assert "private-marker" in capsys.readouterr().out


def test_leak_scan_reports_bad_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, _ = _repo(tmp_path, monkeypatch)
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": "not-a-list"}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    base = _commit_all(repo, "bad markers")
    head = _add_file(repo, "module.py", "code\n")

    code = main(["leak-scan", "--base", base, "--commit", head])

    assert code == 1
    assert "cannot read project config" in capsys.readouterr().err


def test_leak_scan_requires_a_git_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.chdir(plain)

    code = main(["leak-scan", "--base", "HEAD~1", "--commit", "HEAD"])

    assert code == 1
    assert "must be run inside a git repository" in capsys.readouterr().err


def test_leak_scan_binds_to_nested_repo_not_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # An AgentMarshal repo with a plain git repo nested inside it.
    outer = tmp_path / "outer"
    outer.mkdir()
    _git(outer, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(outer)
    assert main(["init"]) == 0
    _commit_all(outer, "outer init")
    inner = outer / "inner"
    inner.mkdir()
    _git(inner, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(inner)
    (inner / "readme.md").write_text("hi\n", encoding="utf-8")
    base = _commit_all(inner, "inner base")
    head = _add_file(inner, "secret.py", "key = 'AKIAIOSFODNN7EXAMPLE'\n")

    # Must scan the inner checkout, not bind to the outer project and run git
    # in the wrong repo.
    code = main(["leak-scan", "--base", base, "--commit", head])

    assert code == 1
    assert "aws-access-key-id" in capsys.readouterr().out


def test_leak_scan_handles_non_utf8_diff_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import os

    repo, base = _repo(tmp_path, monkeypatch)
    # Emit raw bytes for a non-UTF-8 path (default quoting would hide it).
    _git(repo, "config", "core.quotePath", "false")
    bad_path = os.fsencode(repo) + b"/\xff.py"
    with open(bad_path, "wb") as bad_file:
        bad_file.write(b"code\n")
    head = _commit_all(repo, "non-utf8 path")

    code = main(["leak-scan", "--base", base, "--commit", head])

    # A controlled refusal, not a traceback.
    assert code == 1
    assert "non-UTF-8" in capsys.readouterr().err


def test_leak_scan_works_in_plain_git_repo_without_agentmarshal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # No `agentmarshal init`: a plain git repo. Built-in secret signatures
    # must still scan (markers are simply empty).
    repo = tmp_path / "plain-git"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    (repo / "readme.md").write_text("hello\n", encoding="utf-8")
    base = _commit_all(repo, "base")
    head = _add_file(repo, "secret.py", "key = 'AKIAIOSFODNN7EXAMPLE'\n")

    code = main(["leak-scan", "--base", base, "--commit", head])

    assert code == 1
    assert "aws-access-key-id" in capsys.readouterr().out
