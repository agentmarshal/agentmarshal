"""`agentmarshal extension trust|untrust|list` — local run grants for shared
extensions.

ADR-0013 decision 14 / ADR-0014's map / ADR-0022 section 7: a grant approves
the hash of the whole extension directory on one clone, recorded as
`trust.toml` under the clone's local state, and each grant and removal
appends one `trust-changed` event to the process log. Decision 15's bound
stands — nothing here resists a same-user process.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.localstate import LocalState
from agentmarshal.process_log import read_events


@pytest.fixture(autouse=True)
def _isolated_actor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet", "-b", "master"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo


def _extension(
    repo: Path,
    name: str = "openspec",
    files: dict[str, str] | None = None,
) -> Path:
    """A directory-form shared extension with the given files."""

    if files is None:
        files = {
            "manifest.toml": (
                'schema = 2\nname = "openspec"\nversion = "1.0.0"\n'
                'footprint = ["openspec/"]\ndocuments = []\n\n'
                '[[stage]]\nphase = "pre-gate-stop"\ncommand = "bin/run.py"\n'
            ),
            "bin/run.py": "print('runs the check')\n",
            "lock/uv.lock": 'version = 1\nrequires-python = ">=3.12"\n',
        }
    directory = repo / ".agentmarshal" / "extensions" / name
    for relpath, content in files.items():
        path = directory / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return directory


def _trust(name: str = "openspec") -> int:
    return main(["extension", "trust", name])


def _untrust(name: str = "openspec") -> int:
    return main(["extension", "untrust", name])


def _list() -> int:
    return main(["extension", "list"])


def _state(repo: Path) -> LocalState:
    return LocalState(repo / ".git" / "agentmarshal")


def _trust_file(repo: Path) -> Path:
    return _state(repo).trust_file


def _grants(repo: Path) -> dict[str, Any]:
    data = tomllib.loads(_trust_file(repo).read_text(encoding="utf-8"))
    return dict(data.get("grants", {}))


def _events(repo: Path) -> list[dict[str, object]]:
    return read_events(_state(repo))


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _file_hashes(directory: Path) -> dict[str, str]:
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    }


# -- the grant ---------------------------------------------------------------


def test_a_grant_records_the_directory_hash_every_files_hash_the_granter_and_when(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a grant records the directory hash, every file's hash, the granter and when."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    directory = _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    capsys.readouterr()

    assert _trust() == 0

    out = capsys.readouterr().out
    assert str(_trust_file(repo)) in out
    assert "granted openspec" in out
    data = tomllib.loads(_trust_file(repo).read_text(encoding="utf-8"))
    assert data["format"] == 1
    grant = data["grants"]["openspec"]
    assert grant["files"] == _file_hashes(directory)
    assert grant["granted_by"] == "ops-lead"
    assert grant["granted_by_source"] == "override"
    assert datetime.fromisoformat(grant["granted_at"]).tzinfo is not None
    # The directory hash recomputes deterministically from the file list.
    from agentmarshal.extension_trust import _directory_hash

    assert grant["directory_hash"] == _directory_hash(grant["files"])
    assert grant["directory_hash"] in out
    assert "ops-lead" in out


def test_the_directory_hash_covers_the_whole_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the directory hash covers the whole directory."""
    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        files={
            "manifest.toml": 'schema = 2\nname = "openspec"\nversion = "1"\n'
            'footprint = ["x/"]\ndocuments = []\n',
            "bin/run.py": "a = 1\n",
            "lock/uv.lock": "lock\n",
            "docs/deep/nested.txt": "nested\n",
        },
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")

    assert _trust() == 0
    first = _grants(repo)["openspec"]
    assert set(first["files"]) == {
        "manifest.toml",
        "bin/run.py",
        "lock/uv.lock",
        "docs/deep/nested.txt",
    }
    nested = repo / ".agentmarshal" / "extensions" / "openspec" / "docs/deep/nested.txt"
    nested.write_text("changed\n", encoding="utf-8")
    assert _trust() == 0
    second = _grants(repo)["openspec"]
    assert second["directory_hash"] != first["directory_hash"]
    assert (
        second["files"]["docs/deep/nested.txt"]
        != first["files"]["docs/deep/nested.txt"]
    )


def test_a_regrant_replaces_the_earlier_grant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a re-grant replaces the earlier grant."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")

    assert _trust() == 0
    first = _grants(repo)["openspec"]
    run_py = repo / ".agentmarshal" / "extensions" / "openspec" / "bin/run.py"
    run_py.write_text("print('v2')\n", encoding="utf-8")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "other-actor")
    assert _trust() == 0

    grants = _grants(repo)
    assert list(grants) == ["openspec"]
    grant = grants["openspec"]
    assert grant["directory_hash"] != first["directory_hash"]
    assert grant["granted_by"] == "other-actor"


def test_no_resolvable_granter_refuses_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no resolvable granter refuses, writing nothing."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    capsys.readouterr()

    assert _trust() == 1

    err = capsys.readouterr().err
    assert "granter" in err and "AGENTMARSHAL_ACTOR" in err
    assert not _trust_file(repo).exists()
    assert _events(repo) == []


# -- what trust refuses -------------------------------------------------------


def test_a_symbolic_link_inside_the_directory_refuses_the_grant_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a symbolic link inside the directory refuses the grant naming it."""
    repo = _project(tmp_path, monkeypatch)
    directory = _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    outside = repo / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (directory / "bin" / "linked.py").symlink_to(outside)
    capsys.readouterr()

    assert _trust() == 1

    err = capsys.readouterr().err
    assert "bin/linked.py" in err
    assert not _trust_file(repo).exists()
    # A symlinked subdirectory inside refuses the same way, dangling or not.
    (directory / "bin" / "linked.py").unlink()
    (directory / "docs").symlink_to(repo / "missing-target")
    assert _trust() == 1
    assert "docs" in capsys.readouterr().err
    assert not _trust_file(repo).exists()


def test_a_non_regular_file_inside_the_directory_refuses_the_grant_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a non-regular file inside the directory refuses the grant naming it."""
    repo = _project(tmp_path, monkeypatch)
    directory = _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    os.mkfifo(directory / "bin" / "pipe")
    capsys.readouterr()

    assert _trust() == 1

    assert "bin/pipe" in capsys.readouterr().err
    assert not _trust_file(repo).exists()


def test_a_missing_extension_refuses_the_grant_naming_why(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a missing extension refuses the grant naming why."""
    repo = _project(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    capsys.readouterr()

    assert _trust("ghost") == 1

    err = capsys.readouterr().err
    assert "ghost" in err and "missing" in err
    assert not _trust_file(repo).exists()


def test_a_file_form_extension_refuses_the_grant_naming_why(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a file-form extension refuses the grant naming why."""
    repo = _project(tmp_path, monkeypatch)
    file_form = repo / ".agentmarshal" / "extensions" / "declared.toml"
    file_form.parent.mkdir(parents=True, exist_ok=True)
    file_form.write_text(
        'schema = 1\nname = "declared"\nversion = "1"\n'
        'footprint = ["x/"]\ndocuments = []\nartifacts = []\n'
        'install = "i"\nremove = "r"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    capsys.readouterr()

    assert _trust("declared") == 1

    err = capsys.readouterr().err
    assert "declared" in err and "file" in err
    assert not _trust_file(repo).exists()


def test_an_extension_in_both_forms_refuses_the_grant_naming_both_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extension in both forms refuses the grant naming both paths."""
    repo = _project(tmp_path, monkeypatch)
    directory = _extension(repo)
    file_form = repo / ".agentmarshal" / "extensions" / "openspec.toml"
    file_form.write_text("schema = 1\n", encoding="utf-8")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    capsys.readouterr()

    assert _trust() == 1

    err = capsys.readouterr().err
    assert str(file_form) in err
    assert str(directory) in err
    assert not _trust_file(repo).exists()


def test_a_symlinked_extension_directory_refuses_the_grant_as_a_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a symlinked extension directory refuses the grant as a link."""
    repo = _project(tmp_path, monkeypatch)
    real = _extension(repo, name="real")
    extensions = repo / ".agentmarshal" / "extensions"
    (extensions / "openspec").symlink_to(real, target_is_directory=True)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    capsys.readouterr()

    assert _trust() == 1

    assert "symbolic link" in capsys.readouterr().err
    assert not _trust_file(repo).exists()
    # A dangling link at <name> refuses the same way.
    (extensions / "openspec").unlink()
    (extensions / "openspec").symlink_to(extensions / "gone")
    assert _trust() == 1
    assert "symbolic link" in capsys.readouterr().err


def test_a_refused_grant_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a refused grant writes nothing."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    before = _snapshot(_journal(repo))
    capsys.readouterr()

    assert _trust("ghost") == 1

    assert not (repo / ".git" / "agentmarshal").exists()
    assert _snapshot(_journal(repo)) == before


# -- untrust ------------------------------------------------------------------


def test_untrust_removes_the_named_grant_and_keeps_the_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: untrust removes the named grant and keeps the rest."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    _extension(repo, name="other")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    assert _trust("other") == 0
    capsys.readouterr()

    assert _untrust() == 0

    out = capsys.readouterr().out
    assert str(_trust_file(repo)) in out
    assert "openspec" in out
    grants = _grants(repo)
    assert "openspec" not in grants
    assert "other" in grants


def test_untrust_on_a_name_with_no_grant_refuses_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: untrust on a name with no grant refuses naming it."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    before = _trust_file(repo).read_bytes()
    events_before = len(_events(repo))
    capsys.readouterr()

    assert _untrust("other") == 1

    assert "other" in capsys.readouterr().err
    assert _trust_file(repo).read_bytes() == before
    assert len(_events(repo)) == events_before


def test_untrust_works_when_the_extensions_directory_is_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: untrust works when the extension's directory is gone."""
    repo = _project(tmp_path, monkeypatch)
    directory = _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    shutil.rmtree(directory)

    assert _untrust() == 0
    assert _grants(repo) == {}


# -- list ---------------------------------------------------------------------


def test_a_granted_extension_lists_as_granted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a granted extension lists as granted."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    capsys.readouterr()

    assert _list() == 0

    assert capsys.readouterr().out == "openspec: granted\n"


def test_an_extension_with_no_grant_lists_as_not_granted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extension with no grant lists as not granted."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    capsys.readouterr()

    assert _list() == 0

    assert capsys.readouterr().out == "openspec: not granted\n"


def test_a_changed_file_lists_as_changed_after_approval_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a changed file lists as changed after approval naming it."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    run_py = repo / ".agentmarshal" / "extensions" / "openspec" / "bin/run.py"
    run_py.write_text("print('edited')\n", encoding="utf-8")
    capsys.readouterr()

    assert _list() == 0

    out = capsys.readouterr().out
    assert "openspec: changed after approval: bin/run.py (changed)" in out


def test_an_added_file_lists_as_changed_after_approval_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an added file lists as changed after approval naming it."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    added = repo / ".agentmarshal" / "extensions" / "openspec" / "bin/new.py"
    added.write_text("new = True\n", encoding="utf-8")
    capsys.readouterr()

    assert _list() == 0

    out = capsys.readouterr().out
    assert "openspec: changed after approval: bin/new.py (added)" in out


def test_a_removed_file_lists_as_changed_after_approval_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a removed file lists as changed after approval naming it."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    (repo / ".agentmarshal" / "extensions" / "openspec" / "lock/uv.lock").unlink()
    capsys.readouterr()

    assert _list() == 0

    out = capsys.readouterr().out
    assert "openspec: changed after approval: lock/uv.lock (removed)" in out


def test_the_first_differing_file_in_sorted_order_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the first differing file in sorted order is named."""
    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        files={
            "manifest.toml": "m\n",
            "bin/zzz.py": "z\n",
            "aaa.py": "a\n",
        },
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    directory = repo / ".agentmarshal" / "extensions" / "openspec"
    (directory / "bin/zzz.py").write_text("z changed\n", encoding="utf-8")
    (directory / "manifest.toml").write_text("m changed\n", encoding="utf-8")
    (directory / "zzz_added.py").write_text("added\n", encoding="utf-8")
    capsys.readouterr()

    assert _list() == 0

    out = capsys.readouterr().out
    # bin/zzz.py, manifest.toml changed and zzz_added.py added — the
    # first in sorted order is bin/zzz.py.
    assert "changed after approval: bin/zzz.py (changed)" in out


def test_file_form_extensions_are_not_listed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: file-form extensions are not listed."""
    repo = _project(tmp_path, monkeypatch)
    extensions = repo / ".agentmarshal" / "extensions"
    extensions.mkdir(parents=True, exist_ok=True)
    (extensions / "declared.toml").write_text("schema = 1\n", encoding="utf-8")
    capsys.readouterr()

    assert _list() == 0

    assert capsys.readouterr().out == ""


def test_a_directory_that_cannot_be_hashed_is_named_not_hashed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a directory that cannot be hashed is named, not hashed."""
    repo = _project(tmp_path, monkeypatch)
    directory = _extension(repo)
    outside = repo / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (directory / "bin" / "linked.py").symlink_to(outside)
    capsys.readouterr()

    assert _list() == 0

    out = capsys.readouterr().out
    assert (
        "openspec: a symbolic link inside the extension's directory: "
        "bin/linked.py" in out
    )


def test_a_symlinked_extension_directory_is_named_not_hashed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a symlinked extension directory is named, not hashed."""
    repo = _project(tmp_path, monkeypatch)
    real = _extension(repo, name="real")
    (repo / ".agentmarshal" / "extensions" / "linked").symlink_to(
        real, target_is_directory=True
    )
    capsys.readouterr()

    assert _list() == 0

    out = capsys.readouterr().out
    assert "linked: a symbolic link" in out
    assert "real: not granted" in out


def test_no_directory_form_extensions_prints_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no directory-form extensions prints nothing."""
    _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert _list() == 0

    assert capsys.readouterr().out == ""


def test_list_never_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: list never writes."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    before = _snapshot(_journal(repo))
    capsys.readouterr()

    assert _list() == 0

    assert not (repo / ".git" / "agentmarshal").exists()
    assert _snapshot(_journal(repo)) == before


# -- trust.toml ---------------------------------------------------------------


def test_trust_toml_is_written_under_the_clones_local_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: trust.toml is written under the clone's local state."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")

    assert _trust() == 0

    assert _trust_file(repo).is_file()
    assert not (repo / ".agentmarshal" / "trust.toml").exists()
    tracked = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    assert b"trust.toml" not in tracked.stdout


def test_trust_toml_is_replaced_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: trust.toml is replaced atomically."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0

    replaced: list[tuple[str, str]] = []
    real_replace = os.replace

    def record_replace(src: Any, dst: Any) -> None:
        replaced.append((str(src), str(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", record_replace)
    assert _trust() == 0
    assert len(replaced) == 1
    staging, target = replaced[0]
    assert Path(staging).parent == _state(repo).root
    assert staging != target
    assert target == str(_trust_file(repo))
    before_failure = _trust_file(repo).read_bytes()

    def fail_replace(src: Any, dst: Any) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", fail_replace)
    assert _trust() == 1
    # The published file is whole — never a half-written grant — and the
    # staging file is unlinked.
    assert _trust_file(repo).read_bytes() == before_failure
    assert not list(_state(repo).root.glob(".trust-*.tmp"))


@pytest.mark.parametrize("subcommand", ["trust", "untrust", "list"])
def test_a_malformed_trust_toml_refuses_every_subcommand_naming_the_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    subcommand: str,
) -> None:
    """Scenario: a malformed trust.toml refuses every subcommand naming the file."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    _state(repo).root.mkdir(parents=True)
    _trust_file(repo).write_bytes(b"this is not = toml [unclosed")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    capsys.readouterr()

    argv = ["extension", subcommand]
    if subcommand != "list":
        argv.append("openspec")
    assert main(argv) == 1

    err = capsys.readouterr().err
    assert str(_trust_file(repo)) in err


@pytest.mark.parametrize("content", ["format = 2\n", 'format = "one"\n', "[grants]\n"])
@pytest.mark.parametrize("subcommand", ["trust", "untrust", "list"])
def test_an_unknown_format_trust_toml_refuses_every_subcommand_naming_the_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    subcommand: str,
    content: str,
) -> None:
    """Scenario: an unknown-format trust.toml refuses every subcommand naming the file."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    _state(repo).root.mkdir(parents=True)
    _trust_file(repo).write_text(content, encoding="utf-8")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    capsys.readouterr()

    argv = ["extension", subcommand]
    if subcommand != "list":
        argv.append("openspec")
    assert main(argv) == 1

    err = capsys.readouterr().err
    assert str(_trust_file(repo)) in err and "format" in err


def test_a_missing_trust_toml_reads_as_no_grants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a missing trust.toml reads as no grants."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    capsys.readouterr()

    assert _list() == 0

    assert capsys.readouterr().out == "openspec: not granted\n"
    assert _untrust() == 1
    assert "no grant" in capsys.readouterr().err


# -- the trust-changed event ---------------------------------------------------


def test_trust_appends_one_trust_changed_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: trust appends one trust-changed event."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    capsys.readouterr()

    assert _trust() == 0

    events = _events(repo)
    assert len(events) == 1
    event = events[0]
    assert event["event"] == "trust-changed"
    assert event["format"] == 1
    assert event["extension"] == "openspec"
    assert event["action"] == "granted"
    assert event["actor"] == "ops-lead"
    assert event["directory_hash"] == _grants(repo)["openspec"]["directory_hash"]
    assert "task" not in event


def test_untrust_appends_one_trust_changed_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: untrust appends one trust-changed event."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    held_hash = _grants(repo)["openspec"]["directory_hash"]

    assert _untrust() == 0

    removed = [event for event in _events(repo) if event.get("action") == "removed"]
    assert len(removed) == 1
    event = removed[0]
    assert event["event"] == "trust-changed"
    assert event["extension"] == "openspec"
    assert event["directory_hash"] == held_hash
    assert event["actor"] == "ops-lead"


def test_a_refused_command_appends_no_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a refused command appends no event."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")

    assert _trust("ghost") == 1
    assert _untrust("openspec") == 1

    assert _events(repo) == []


# -- the boundaries ------------------------------------------------------------


def test_no_file_in_the_extensions_directory_is_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: no file in the extension's directory is run."""
    repo = _project(tmp_path, monkeypatch)
    sentinel = repo / "sentinel"
    directory = _extension(
        repo,
        files={
            "manifest.toml": "m\n",
            "bin/run.py": (
                f"import pathlib\npathlib.Path({str(sentinel)!r}).write_text('ran')\n"
            ),
        },
    )
    (directory / "bin/run.py").chmod(0o755)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")

    assert _trust() == 0
    assert _list() == 0
    assert _untrust() == 0

    assert not sentinel.exists()


def test_the_journal_is_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the journal is untouched."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    before = _snapshot(_journal(repo))

    assert _trust() == 0
    assert _list() == 0
    assert _untrust() == 0

    assert _snapshot(_journal(repo)) == before


def test_the_extension_group_takes_trust_untrust_and_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the extension group takes trust, untrust and list."""
    _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert _list() == 0
    with pytest.raises(SystemExit):
        main(["extension"])
    with pytest.raises(SystemExit):
        main(["extension", "bogus"])
    with pytest.raises(SystemExit):
        main(["extension", "trust"])
