"""Tests for embedded and sidecar journal root resolution."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.placement import PlacementError, resolve_placement


def _git_init(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=path, check=True)


def test_missing_placement_resolves_as_embedded(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".agentmarshal").mkdir(parents=True)
    (project / ".agentmarshal" / "project.json").write_text(
        '{"schema": 1}\n', encoding="utf-8"
    )

    placement = resolve_placement(project, require_host=True)

    assert placement.kind == "embedded"
    assert placement.journal_root == project / ".agentmarshal" / "journal"
    assert placement.host_root == project


def test_init_host_records_sidecar_and_resolved_git_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    _git_init(host)
    _git_init(sidecar)
    nested = host / "src"
    nested.mkdir()
    monkeypatch.chdir(sidecar)

    assert main(["init", "--host", str(nested)]) == 0

    project = json.loads(
        (sidecar / ".agentmarshal" / "project.json").read_text(encoding="utf-8")
    )
    assert project["placement"] == "sidecar"
    assert project["host"] == str(host.resolve())
    placement = resolve_placement(sidecar, require_host=True)
    assert placement.journal_root == sidecar / ".agentmarshal" / "journal"
    assert placement.host_root == host


@pytest.mark.parametrize("host_kind", ["missing", "non-git"])
def test_sidecar_host_failure_names_path_and_reason(
    tmp_path: Path, host_kind: str
) -> None:
    sidecar = tmp_path / "sidecar"
    _git_init(sidecar)
    host = tmp_path / host_kind
    if host_kind == "non-git":
        host.mkdir()
    (sidecar / ".agentmarshal").mkdir()
    (sidecar / ".agentmarshal" / "project.json").write_text(
        json.dumps({"schema": 1, "placement": "sidecar", "host": str(host)}),
        encoding="utf-8",
    )

    with pytest.raises(PlacementError) as raised:
        resolve_placement(sidecar, require_host=True)

    assert str(host) in str(raised.value)
    reason = "does not exist" if host_kind == "missing" else "not a git worktree"
    assert reason in str(raised.value)


def test_a_sidecar_may_not_be_a_worktree_of_its_own_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Outside the host's tree is not enough to be outside the host's repository.

    A linked worktree of the host sits elsewhere on disk, so a path check
    passes — while its commits land in the host's object database, which is
    exactly what ADR-0008 Decision 3 forbids.
    """

    from agentmarshal.cli import main

    host = tmp_path / "host"
    host.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=host, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=T",
            "-c",
            "user.email=t@t.invalid",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "base",
        ],
        cwd=host,
        check=True,
    )
    sidecar = tmp_path / "sidecar"
    subprocess.run(
        ["git", "worktree", "add", "--quiet", "-b", "journal", str(sidecar)],
        cwd=host,
        check=True,
    )
    monkeypatch.chdir(sidecar)

    assert main(["init", "--host", str(host)]) == 1

    error = capsys.readouterr().err
    assert "worktree of host" in error
    assert not (sidecar / ".agentmarshal").exists()
