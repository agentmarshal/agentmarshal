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


def test_abandon_in_a_sidecar_writes_to_the_sidecar_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pinned against a review claim that it wrote to the host's journal.

    In a sidecar the project root *is* the sidecar root, so deriving the
    journal from it is correct — the claim misread which root the CLI passes.
    Disproved by running it; kept as a test so the misreading cannot recur.
    """

    from agentmarshal.cli import main

    host = tmp_path / "host"
    _git_init(host)
    sidecar = tmp_path / "sidecar"
    _git_init(sidecar)
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    assert main(["open", "--title", "Probe", "--scope", "src/"]) == 0

    assert main(["abandon", "--task", "CR-001", "--reason", "probe"]) == 0

    records = sidecar / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    assert [path.name for path in records.glob("*-abandoned.json")]
    assert not (host / ".agentmarshal").exists()


def test_a_sidecar_inside_the_hosts_git_directory_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Pinned against a review claim that this path was allowed.

    `host/.git/x` is relative to the host worktree, so the existing check
    already refuses it. Disproved by running it; pinned so the guard cannot be
    narrowed later without noticing.
    """

    from agentmarshal.cli import main

    host = tmp_path / "host"
    _git_init(host)
    inside = host / ".git" / "sneaky"
    inside.mkdir(parents=True)
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=inside, check=True)
    monkeypatch.chdir(inside)

    assert main(["init", "--host", str(host)]) == 1

    assert "must live outside host worktree" in capsys.readouterr().err


def _tree_snapshot(root: Path) -> dict[str, tuple[int, bytes]]:
    return {
        str(path.relative_to(root)): (path.stat().st_mode, path.read_bytes())
        for path in root.rglob("*")
        if path.is_file()
    }


def _commit(path: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Worker",
            "-c",
            "user.email=worker@test.invalid",
            "commit",
            "--quiet",
            "-m",
            message,
        ],
        cwd=path,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        encoding="utf-8",
    ).stdout.strip()


def test_sidecar_gate_complete_and_leak_scan_read_only_the_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    _git_init(host)
    _git_init(sidecar)
    (host / "README.md").write_text("host\n", encoding="utf-8")
    base = _commit(host, "base")
    (host / "src").mkdir()
    (host / "src" / "change.py").write_text(
        "key = 'AKIAIOSFODNN7EXAMPLE'\n", encoding="utf-8"
    )
    head = _commit(host, "implement")

    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    assert main(["open", "--title", "Sidecar gate", "--scope", "src/"]) == 0
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--verdict",
                "approved",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test",
                "--email",
                "reviewer@test.invalid",
            ]
        )
        == 0
    )
    capsys.readouterr()
    before = _tree_snapshot(host)
    gate_args = [
        "--task",
        "CR-001",
        "--commit",
        head,
        "--base",
        base,
        "--pipeline-sha",
        head,
    ]

    assert main(["gate", *gate_args]) == 0
    gate_output = capsys.readouterr().out
    assert "Sidecar checks are advisory and decide no merge." in gate_output
    assert "gate: passed" not in gate_output
    assert main(["complete", *gate_args]) == 0
    complete_output = capsys.readouterr().out
    assert "Sidecar checks are advisory and decide no merge." in complete_output
    assert "gate: passed" not in complete_output
    records = sidecar / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    assert list(records.glob("*-completed.json"))

    assert main(["status", "CR-001"]) == 0
    status_output = capsys.readouterr()
    assert "Placement: sidecar" in status_output.err
    assert main(["report", "--task", "CR-001"]) == 0
    report_output = capsys.readouterr()
    assert "Placement: sidecar" in report_output.err

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1
    assert "possible leak categories" in capsys.readouterr().out
    assert _tree_snapshot(host) == before
