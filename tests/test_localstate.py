"""Tests for where a clone's local state lives (ADR-0014 decisions 4 and 5)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.journal.placement import resolve_placement
from agentmarshal.localstate import (
    LocalStateError,
    ensure_directory,
    local_state,
)


def _git_init(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=path, check=True)


def _commit(path: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=T",
            "-c",
            "user.email=t@t.invalid",
            "commit",
            "--quiet",
            "-m",
            message,
        ],
        cwd=path,
        check=True,
    )


def _init_project(path: Path, *, host: Path | None = None) -> None:
    (path / ".agentmarshal").mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {"schema": 1}
    if host is not None:
        data["placement"] = "sidecar"
        data["host"] = str(host)
    (path / ".agentmarshal" / "project.json").write_text(
        json.dumps(data) + "\n", encoding="utf-8"
    )


def _tree_snapshot(root: Path) -> dict[str, tuple[int, bytes | None]]:
    return {
        str(path.relative_to(root)): (
            path.stat().st_mode,
            path.read_bytes() if path.is_file() else None,
        )
        for path in root.rglob("*")
    }


def test_embedded_project_resolves_under_its_own_git_dir(tmp_path: Path) -> None:
    """Scenario: an embedded project resolves under its own git directory."""

    project = tmp_path / "project"
    _git_init(project)
    _init_project(project)

    state = local_state(resolve_placement(project))

    assert state.root == project.resolve() / ".git" / "agentmarshal"


def test_every_named_location_sits_under_the_root(tmp_path: Path) -> None:
    """Scenario: every named location sits under the root."""

    project = tmp_path / "project"
    _git_init(project)
    _init_project(project)

    state = local_state(resolve_placement(project))

    assert state.log == state.root / "log"
    assert state.extensions == state.root / "extensions"
    assert state.deps == state.root / "deps"
    assert state.trust_file == state.root / "trust.toml"
    assert state.switches_file == state.root / "switches.toml"
    assert state.plan_file == state.root / "plan.toml"


def test_linked_worktree_resolves_to_the_shared_location(tmp_path: Path) -> None:
    """Scenario: a linked worktree resolves to the shared location."""

    project = tmp_path / "project"
    _git_init(project)
    _init_project(project)
    _commit(project, "project file")
    linked = tmp_path / "linked"
    subprocess.run(
        ["git", "worktree", "add", "--quiet", str(linked)],
        cwd=project,
        check=True,
    )

    main_state = local_state(resolve_placement(project))
    linked_state = local_state(resolve_placement(linked))

    assert linked_state.root == main_state.root


def test_sidecar_resolves_to_the_journal_repository(tmp_path: Path) -> None:
    """Scenario: a sidecar resolves to the journal repository's git directory."""

    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    _git_init(host)
    _git_init(sidecar)
    _init_project(sidecar, host=host)

    state = local_state(resolve_placement(sidecar, require_host=True))

    assert state.root == sidecar.resolve() / ".git" / "agentmarshal"


def test_host_is_unchanged_after_resolving_and_creating_everything(
    tmp_path: Path,
) -> None:
    """Scenario: the host is unchanged after resolving and creating every location.

    The snapshot covers the host's working tree and its git directory
    together: `.git/` is inside the tree `rglob` walks.
    """

    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    _git_init(host)
    _git_init(sidecar)
    _init_project(sidecar, host=host)
    before = _tree_snapshot(host)

    state = local_state(resolve_placement(sidecar, require_host=True))
    ensure_directory(state.root)
    ensure_directory(state.log)
    ensure_directory(state.extensions)
    ensure_directory(state.deps)
    state.trust_file.write_text("", encoding="utf-8")
    state.switches_file.write_text("", encoding="utf-8")
    state.plan_file.write_text("", encoding="utf-8")

    assert _tree_snapshot(host) == before
    assert state.log.is_dir()
    assert state.trust_file.is_file()


def test_resolving_leaves_no_trace_on_disk(tmp_path: Path) -> None:
    """Scenario: resolving leaves no trace on disk."""

    project = tmp_path / "project"
    _git_init(project)
    _init_project(project)

    state = local_state(resolve_placement(project))

    assert not state.root.exists()
    assert not state.log.exists()
    assert not state.trust_file.exists()
    assert list((project / ".git").glob("agentmarshal*")) == []


def test_a_writer_creates_a_directory_location_explicitly(tmp_path: Path) -> None:
    """Scenario: a writer creates a directory location explicitly."""

    project = tmp_path / "project"
    _git_init(project)
    _init_project(project)
    state = local_state(resolve_placement(project))

    created = ensure_directory(state.log)

    assert created == state.log
    assert state.log.is_dir()
    assert state.root.is_dir()


def test_a_project_outside_git_fails_cleanly(tmp_path: Path) -> None:
    """Scenario: a project outside git fails cleanly."""

    project = tmp_path / "project"
    project.mkdir()
    _init_project(project)

    with pytest.raises(LocalStateError) as raised:
        local_state(resolve_placement(project))

    message = str(raised.value)
    assert str(project.resolve()) in message
    assert "common directory" in message
    assert "not a git repository" in message


def test_a_stale_git_pointer_reports_gits_reason(tmp_path: Path) -> None:
    """Scenario: a project outside git fails cleanly — git's own reason.

    A `.git` file pointing at a missing directory is a case where the
    canned "(not a git worktree)" would be false: whatever words this git
    uses for the refusal are the reason the failure must repeat, so the
    test asks git the same question rather than guessing its wording —
    git's phrasing differs between versions.
    """

    project = tmp_path / "project"
    project.mkdir()
    _init_project(project)
    (project / ".git").write_text(
        f"gitdir: {tmp_path / 'missing-gitdir'}\n", encoding="utf-8"
    )

    gits_reason = (
        subprocess.run(
            [
                "git",
                "-C",
                str(project),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ],
            capture_output=True,
            check=False,
        )
        .stderr.decode("utf-8", errors="replace")
        .strip()
    )

    with pytest.raises(LocalStateError) as raised:
        local_state(resolve_placement(project))

    message = str(raised.value)
    assert str(project.resolve()) in message
    assert "git cannot name a common directory" in message
    assert gits_reason != ""
    assert gits_reason in message
    assert "not a git worktree" not in message
