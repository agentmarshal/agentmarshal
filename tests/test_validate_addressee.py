"""Tests for validate's "addressee not found" warning (CR-214).

ADR-0013 decision 18: a kind no manifest declares draws a warning — not
a refusal — because a record can outlive the manifest that declared its
kind.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import validate as validate_module
from agentmarshal.journal.extensions import ExtensionManifestError
from agentmarshal.journal.records import create_ext_record, write_record
from agentmarshal.journal.validate import validate_journal
from test_journal import initialize_status_repo

_COMMIT = "a" * 40
_PAYLOAD = {"outcome": "clean"}


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tasks: int = 1) -> Path:
    """An initialized repo holding *tasks* open tasks and no extensions."""

    repo = tmp_path / "repo"
    initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    for index in range(tasks):
        assert main(["open", "--title", f"Task {index}"]) == 0
    return repo


def _ext(repo: Path, task: str, kind: str) -> None:
    """Append one `ext` record of *kind* to *task*'s journal records."""

    write_record(
        repo / ".agentmarshal" / "journal",
        task,
        create_ext_record(task, "test", kind, _COMMIT, _PAYLOAD),
    )


def _manifest(
    repo: Path,
    name: str,
    kinds: tuple[str, ...],
    *,
    directory: bool = False,
) -> Path:
    """Write *name*'s manifest — the file form, or the directory form."""

    extensions = repo / ".agentmarshal" / "extensions"
    path = (
        extensions / name / "manifest.toml"
        if directory
        else extensions / f"{name}.toml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    declared = ", ".join(json.dumps(kind) for kind in kinds)
    path.write_text(
        "schema = 2\n"
        f'name = "{name}"\n'
        'version = "1.0.0"\n'
        f'footprint = ["{name}/"]\n'
        "documents = []\n"
        "[records]\n"
        f"kinds = [{declared}]\n",
        encoding="utf-8",
    )
    return path


def test_an_ext_record_whose_kind_no_manifest_declares_draws_an_addressee_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario:
    an ext record whose kind no manifest declares draws an addressee warning."""

    repo = _project(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    _ext(repo, "CR-001", "gone/kind@1")

    report = validate_journal(repo)

    warnings = [line for line in report.lines if line.startswith("WARN")]
    assert len(warnings) == 1
    record_id = next(
        path.name.split("-", 1)[0]
        for path in (
            repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
        ).glob("*-ext.json")
    )
    assert warnings[0] == (
        f"WARN: CR-001: ext record {record_id} kind 'gone/kind@1': addressee not found"
    )
    assert "OK: CR-001" in "\n".join(report.lines)


def test_a_kind_the_manifest_does_not_declare_draws_an_addressee_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a kind the manifest does not declare draws an addressee warning."""

    repo = _project(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    _manifest(repo, "tooling", ("tooling/check@1",))
    _ext(repo, "CR-001", "tooling/other@1")

    report = validate_journal(repo)

    warnings = [line for line in report.lines if line.startswith("WARN")]
    assert len(warnings) == 1
    assert "kind 'tooling/other@1'" in warnings[0]
    assert "addressee not found" in warnings[0]


def test_a_kind_declared_in_the_file_form_draws_no_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a kind declared in the file form draws no warning."""

    repo = _project(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    _manifest(repo, "tooling", ("tooling/check@1",))
    _ext(repo, "CR-001", "tooling/check@1")

    report = validate_journal(repo)

    assert report.passed, report.lines
    assert not any(line.startswith("WARN") for line in report.lines)


def test_a_kind_declared_in_the_directory_form_draws_no_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a kind declared in the directory form draws no warning."""

    repo = _project(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    _manifest(repo, "linter", ("linter/run@1",), directory=True)
    _ext(repo, "CR-001", "linter/run@1")

    report = validate_journal(repo)

    assert report.passed, report.lines
    assert not any(line.startswith("WARN") for line in report.lines)


def test_a_manifest_that_cannot_be_read_is_named_once_and_declares_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a manifest that cannot be read is named once and declares nothing.

    Three records across two tasks name the extension whose manifest is
    malformed: the manifest is named on exactly one WARN line, and every
    record still draws its own addressee warning — the unreadable
    manifest's kinds count as undeclared.
    """

    repo = _project(tmp_path, monkeypatch, tasks=2)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    extensions = repo / ".agentmarshal" / "extensions"
    extensions.mkdir()
    (extensions / "borked.toml").write_text("schema = 2\nname = [oops\n")
    _ext(repo, "CR-001", "borked/x@1")
    _ext(repo, "CR-001", "borked/y@1")
    _ext(repo, "CR-002", "borked/z@1")

    report = validate_journal(repo)

    manifest_warnings = [line for line in report.lines if "extension manifest" in line]
    assert len(manifest_warnings) == 1
    assert "borked" in manifest_warnings[0]
    assert "cannot be read" in manifest_warnings[0]
    addressee_warnings = [
        line for line in report.lines if "addressee not found" in line
    ]
    assert len(addressee_warnings) == 3
    assert report.passed, report.lines


def test_the_warning_changes_neither_verdict_nor_exit_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the warning changes neither verdict nor exit status."""

    repo = _project(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    _ext(repo, "CR-001", "gone/kind@1")

    report = validate_journal(repo)
    assert report.passed
    assert any(line.startswith("WARN") for line in report.lines)

    capsys.readouterr()
    assert main(["validate"]) == 0
    output = capsys.readouterr()
    assert "addressee not found" in output.out
    assert "validate: passed" in output.out


def test_a_journal_with_no_ext_records_reads_no_manifests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a journal with no ext records reads no manifests.

    The output is pinned byte for byte to what validate printed before
    the check existed, and the manifest reader is armed to fail the test
    if it is so much as called.
    """

    repo = _project(tmp_path, monkeypatch, tasks=2)
    calls: list[str] = []

    def spy(project_root: Path, name: str) -> object:
        calls.append(name)
        raise AssertionError("a manifest was read")

    monkeypatch.setattr(validate_module, "read_extension_manifest", spy)

    report = validate_journal(repo)

    assert report.passed
    assert calls == []
    assert report.lines == [
        "OK: CR-001 (open, 1 records)",
        "OK: CR-002 (open, 1 records)",
    ]


def test_a_value_on_a_warning_line_is_escaped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a value on a warning line is escaped.

    Every record- or manifest-derived value reaching the WARN lines is
    constrained before it is printed, so the manifest error is the one
    carrier that can hold a line-forging character; here it is made to
    carry one, and it prints as its escape on the warning's own line.
    """

    repo = _project(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    _ext(repo, "CR-001", "gone/kind@1")

    def unreadable(project_root: Path, name: str) -> object:
        raise ExtensionManifestError("resolving failed\nFAIL: forged")

    monkeypatch.setattr(validate_module, "read_extension_manifest", unreadable)

    report = validate_journal(repo)

    manifest_warning = next(
        line for line in report.lines if "extension manifest" in line
    )
    assert "\\n" in manifest_warning
    assert "FAIL: forged" in manifest_warning
    for line in report.lines:
        assert "\n" not in line and "\r" not in line
