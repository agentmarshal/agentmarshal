"""``doctor`` lists the shared extensions — ADR-0013 decision 14, section F.

The extensions section prints on stderr beside the paths report: each
shared extension under ``.agentmarshal/extensions/`` of the working
tree — name, form, manifest schema, stages' modes and declared ``ext``
kinds — and, for the directory form, this clone's grant state by the
computation ``extension list`` runs (CR-209). An unreadable manifest
fails a check of its own, the way a malformed project setting does.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import agentmarshal.doctor as doctor
from agentmarshal.cli import main
from agentmarshal.journal.placement import Placement
from agentmarshal.localstate import LocalState, LocalStateError


@pytest.fixture(autouse=True)
def clear_precondition_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep doctor checks independent of the test runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    # Give the repository an identity of its own, the way test_doctor.py's
    # fixture does: without one these tests read whatever the machine has
    # configured, and CI runs them with neither actor variable nor global
    # git identity.
    for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
        subprocess.run(["git", "config", key, value], cwd=repo, check=True)


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    _init_repo(repo)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def _every_precondition_met(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workflow = repo / ".github" / "workflows" / "governance.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "jobs:\n  validate:\n    run: agentmarshal validate\n", encoding="utf-8"
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "implementation-agent")
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", "reviewer --model {model} {prompt_file}"
    )


def _file_extension(
    repo: Path, name: str = "declared", manifest: str | None = None
) -> Path:
    """A file-form shared extension at ``<name>.toml``."""

    path = repo / ".agentmarshal" / "extensions" / f"{name}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        manifest
        if manifest is not None
        else (
            "schema = 1\n"
            f'name = "{name}"\n'
            'version = "1.2.3"\n'
            'footprint = ["openspec/"]\n'
            'documents = ["openspec/specs/"]\n'
            "artifacts = []\n"
            'install = "npx openspec init"\n'
            'remove = "rm -rf openspec"\n'
        ),
        encoding="utf-8",
    )
    return path


def _dir_extension(
    repo: Path,
    name: str = "openspec",
    manifest: str | None = None,
    extra: dict[str, str] | None = None,
) -> Path:
    """A directory-form shared extension at ``<name>/manifest.toml``."""

    directory = repo / ".agentmarshal" / "extensions" / name
    files = {
        "manifest.toml": manifest
        if manifest is not None
        else (
            "schema = 2\n"
            f'name = "{name}"\n'
            'version = "1.0.0"\n'
            'footprint = ["openspec/"]\n'
            'documents = ["openspec/specs/"]\n'
            "\n"
            "[[stage]]\n"
            'phase = "pre-gate-stop"\n'
            'command = "bin/run.py"\n'
            "\n"
            "[records]\n"
            f'kinds = ["{name}/change-archived@1"]\n'
        ),
        "bin/run.py": "print('runs the check')\n",
        "lock/uv.lock": 'version = 1\nrequires-python = ">=3.12"\n',
    }
    files.update(extra or {})
    for relpath, content in files.items():
        path = directory / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return directory


def _state(repo: Path) -> LocalState:
    return LocalState((repo / ".git").resolve() / "agentmarshal")


def _trust(name: str = "openspec") -> int:
    return main(["extension", "trust", name])


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


# -- the section ---------------------------------------------------------------


def test_a_file_form_extension_is_listed_with_its_form_and_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a file-form extension is listed with its form and schema."""
    repo = _project(tmp_path, monkeypatch)
    _file_extension(repo)

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    assert (
        "extension declared: file form, manifest schema 1, "
        "stages: none, ext kinds: none" in err
    )


def test_a_directory_form_extension_is_listed_with_its_stages_modes_and_declared_kinds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a directory-form extension is listed with its stages' modes and declared kinds."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _dir_extension(repo)

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    assert (
        "extension openspec: directory form, manifest schema 2, "
        "stages: pre-gate-stop, ext kinds: openspec/change-archived@1, "
        "grant: not granted" in err
    )


def test_extensions_are_listed_in_sorted_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: extensions are listed in sorted order."""
    repo = _project(tmp_path, monkeypatch)
    _dir_extension(repo, name="zed")
    _file_extension(repo, name="alpha")
    _dir_extension(repo, name="mid")

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    lines = [line for line in err.splitlines() if line.startswith("extension ")]
    assert [line.split(":")[0] for line in lines] == [
        "extension alpha",
        "extension mid",
        "extension zed",
    ]


def test_a_name_held_in_both_forms_is_listed_once_with_the_readers_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a name held in both forms is listed once with the reader's refusal."""
    repo = _project(tmp_path, monkeypatch)
    directory = _dir_extension(repo)
    _file_extension(repo, name="openspec")

    assert main(["doctor"]) == 1

    captured = capsys.readouterr()
    lines = [
        line for line in captured.err.splitlines() if line.startswith("extension ")
    ]
    assert len(lines) == 1
    assert "extension openspec:" in lines[0]
    assert "both the file and the directory form" in lines[0]
    assert "openspec.toml" in lines[0]
    assert str(directory / "manifest.toml") in lines[0]


def test_the_section_prints_on_stderr_escaped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the section prints on stderr, escaped."""
    repo = _project(tmp_path, monkeypatch)
    # A name carrying a character the forgeable-text rule refuses: the
    # reader refuses it at the boundary, and both the check's line and
    # the section's print it escaped.
    forged = "for\nmed"
    (repo / ".agentmarshal" / "extensions" / forged).mkdir(parents=True)

    assert main(["doctor"]) == 1

    captured = capsys.readouterr()
    assert "extension manifest for\\nmed" in captured.out
    assert "extension for\\nmed:" in captured.err
    assert "for\nmed" not in captured.out
    assert "for\nmed" not in captured.err


# -- the grant state ------------------------------------------------------------


def test_a_granted_extension_reports_granted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a granted extension reports granted."""
    repo = _project(tmp_path, monkeypatch)
    _dir_extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    capsys.readouterr()

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    assert "extension openspec: directory form" in err
    assert "grant: granted" in err


def test_an_extension_with_no_grant_reports_not_granted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extension with no grant reports not granted."""
    repo = _project(tmp_path, monkeypatch)
    _dir_extension(repo)

    assert main(["doctor"]) == 0

    assert "grant: not granted" in capsys.readouterr().err


def test_a_file_changed_after_approval_is_named_with_its_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a file changed after approval is named with its kind."""
    repo = _project(tmp_path, monkeypatch)
    directory = _dir_extension(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    (directory / "bin" / "run.py").write_text("print('edited')\n", encoding="utf-8")
    (directory / "bin" / "new.py").write_text("new = True\n", encoding="utf-8")
    (directory / "lock" / "uv.lock").unlink()
    capsys.readouterr()

    assert main(["doctor"]) == 0

    # bin/new.py added, bin/run.py changed, lock/uv.lock removed — the
    # first differing file in sorted order is bin/new.py.
    assert (
        "grant: changed after approval: bin/new.py (added)" in capsys.readouterr().err
    )


def test_a_grant_state_never_changes_doctors_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a grant state never changes doctor's verdict."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    directory = _dir_extension(repo, name="openspec")

    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "grant: not granted" in captured.err
    assert "Summary: all 11 checks passed" in captured.out

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust() == 0
    (directory / "bin" / "run.py").write_text("print('edited')\n", encoding="utf-8")
    capsys.readouterr()

    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "grant: changed after approval: bin/run.py (changed)" in captured.err
    assert "Summary: all 11 checks passed" in captured.out


def test_a_symbolic_link_extension_directory_is_named_not_hashed_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a symbolic-link extension directory is named, not hashed through."""
    repo = _project(tmp_path, monkeypatch)
    real = _dir_extension(repo, name="real")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    assert _trust("real") == 0
    (repo / ".agentmarshal" / "extensions" / "linked").symlink_to(
        real, target_is_directory=True
    )
    capsys.readouterr()

    assert main(["doctor"]) == 1

    captured = capsys.readouterr()
    lines = [
        line for line in captured.err.splitlines() if line.startswith("extension ")
    ]
    linked = next(line for line in lines if line.startswith("extension linked:"))
    assert "symlink" in linked
    assert "grant:" not in linked
    # The real directory still reports its grant — the link cost it nothing.
    real_line = next(line for line in lines if line.startswith("extension real:"))
    assert "grant: granted" in real_line


def test_a_directory_that_cannot_be_hashed_carries_the_reason_in_its_grant_position(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a directory that cannot be hashed carries the reason in its grant position."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    directory = _dir_extension(repo)
    outside = repo / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (directory / "docs").symlink_to(outside)

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    assert "extension openspec: directory form" in err
    assert "grant: a symbolic link inside the extension's directory: docs" in err


def test_a_grants_file_or_local_state_that_cannot_be_read_is_named_not_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a grants file or local state that cannot be read is named, not failed."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _dir_extension(repo)
    _state(repo).root.mkdir(parents=True)
    _state(repo).trust_file.write_bytes(b"this is not = toml [unclosed")

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    assert "grant: unavailable (" in err
    assert str(_state(repo).trust_file) in err

    # And a local state that did not resolve degrades the same way.
    def refuse(_placement: Placement) -> LocalState:
        raise LocalStateError(f"{repo}: git cannot name a common directory")

    monkeypatch.setattr(doctor, "local_state", refuse)
    assert main(["doctor"]) == 0
    err = capsys.readouterr().err
    assert "grant: unavailable (" in err
    assert "git cannot name a common directory" in err


# -- the unreadable manifest ----------------------------------------------------


def test_an_unreadable_manifest_fails_a_check_of_its_own_naming_the_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unreadable manifest fails a check of its own naming the reason."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _file_extension(repo, manifest="this is not = toml [unclosed\n")

    assert main(["doctor"]) == 1

    out = capsys.readouterr().out
    assert "FAIL: extension manifest declared — " in out
    assert "invalid TOML" in out
    assert "1 check(s) failed" in out


def test_an_unreadable_manifest_is_named_on_one_section_line_and_stops_nothing_else(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unreadable manifest is named on one section line and stops nothing else."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _file_extension(
        repo,
        name="broken",
        manifest='schema = 1\nname = "other"\nversion = "1"\n'
        "footprint = []\ndocuments = []\nartifacts = []\n"
        'install = "i"\nremove = "r"\n',
    )
    _dir_extension(repo, name="fine")

    assert main(["doctor"]) == 1

    captured = capsys.readouterr()
    lines = [
        line for line in captured.err.splitlines() if line.startswith("extension ")
    ]
    broken = next(line for line in lines if line.startswith("extension broken:"))
    assert "does not match" in broken
    fine = next(line for line in lines if line.startswith("extension fine:"))
    assert "directory form, manifest schema 2" in fine
    # The other checks still ran and passed; only the one manifest failed.
    assert "OK: extension manifest fine" in captured.out
    assert "OK: project schema" in captured.out
    assert "FAIL: extension manifest broken" in captured.out
    assert "1 check(s) failed" in captured.out


def test_a_discovered_directory_without_a_manifest_is_reported_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a discovered directory without a manifest is reported missing."""
    repo = _project(tmp_path, monkeypatch)
    directory = repo / ".agentmarshal" / "extensions" / "openspec"
    directory.mkdir(parents=True)
    (directory / "bin").mkdir()

    assert main(["doctor"]) == 1

    captured = capsys.readouterr()
    assert "FAIL: extension manifest openspec — " in captured.out
    assert "missing" in captured.out
    lines = [
        line for line in captured.err.splitlines() if line.startswith("extension ")
    ]
    assert len(lines) == 1
    assert "extension openspec:" in lines[0] and "missing" in lines[0]
    # A real directory still reports its grant state on the same line.
    assert "grant: not granted" in lines[0]


def test_a_listing_that_cannot_be_produced_fails_one_check_naming_the_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a listing that cannot be produced fails one check naming the reason."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    extensions = repo / ".agentmarshal" / "extensions"
    extensions.symlink_to(elsewhere, target_is_directory=True)

    assert main(["doctor"]) == 1

    captured = capsys.readouterr()
    assert "FAIL: extension manifests — " in captured.out
    assert "symbolic link" in captured.out
    assert "1 check(s) failed" in captured.out
    assert "extensions: unavailable (" in captured.err
    assert "symbolic link" in captured.err


def test_a_project_that_cannot_be_found_marks_the_section_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a project that cannot be found marks the section unavailable."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    assert main(["doctor"]) == 1

    err = capsys.readouterr().err
    assert "extensions: unavailable (" in err
    assert "local state: unavailable (" in err


# -- no extensions --------------------------------------------------------------


def test_no_extensions_directory_prints_one_line_saying_there_are_no_extensions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no extensions directory prints one line saying there are no extensions."""  # noqa: E501
    _project(tmp_path, monkeypatch)

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    assert "extensions: none" in captured.err
    assert captured.err.count("extensions:") == 1
    assert "extension manifest" not in captured.out


def test_doctors_other_output_is_unchanged_without_extensions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: doctor's other output is unchanged without extensions."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    assert captured.out.count("OK:") == 10
    assert "Summary: all 10 checks passed" in captured.out
    # An extensions directory holding no extension prints the same line.
    (repo / ".agentmarshal" / "extensions").mkdir()
    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert "extensions: none" in captured.err
    assert "Summary: all 10 checks passed" in captured.out


# -- the boundaries -------------------------------------------------------------


def test_no_file_an_extension_declares_is_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no file an extension declares is run."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    sentinel = repo / "sentinel"
    _dir_extension(
        repo,
        extra={
            "bin/run.py": (
                f"import pathlib\npathlib.Path({str(sentinel)!r}).write_text('ran')\n"
            )
        },
    )
    (repo / ".agentmarshal" / "extensions" / "openspec" / "bin" / "run.py").chmod(0o755)
    capsys.readouterr()

    assert main(["doctor"]) == 0

    assert not sentinel.exists()
    assert "stages: pre-gate-stop" in capsys.readouterr().err


def test_the_listing_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the listing writes nothing."""
    repo = _project(tmp_path, monkeypatch)
    _dir_extension(repo)
    _journal(repo).mkdir(parents=True)
    before = _snapshot(_journal(repo))
    capsys.readouterr()

    assert main(["doctor"]) == 0

    capsys.readouterr()
    assert not (repo / ".git" / "agentmarshal").exists()
    assert _snapshot(_journal(repo)) == before


def test_the_extension_names_helper_keeps_links_and_skips_strays(
    tmp_path: Path,
) -> None:
    """Discovery keeps a link under its name and skips a stray file.

    Not a spec scenario — the helper's own seam: a link at ``<name>``
    or ``<name>.toml`` is found under its name so the reader's refusal
    reports it, and an entry that is neither a directory nor a manifest
    path is not an extension at all.
    """

    managed = tmp_path / "extensions"
    managed.mkdir()
    (managed / "real").mkdir()
    (managed / "filed.toml").write_text("x\n", encoding="utf-8")
    (managed / "linked").symlink_to(managed / "real", target_is_directory=True)
    (managed / "linked.toml").symlink_to(managed / "filed.toml")
    (managed / "stray.txt").write_text("x\n", encoding="utf-8")
    (managed / "plain").write_text("x\n", encoding="utf-8")

    # `linked` and `linked.toml` are one name; `plain` and `stray.txt`
    # are no extension's manifest path.
    assert doctor._extension_names(managed) == ["filed", "linked", "real"]
