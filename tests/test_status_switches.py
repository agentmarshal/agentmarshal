"""``status`` names each switched-off shared extension — ADR-0013 D17.

ADR-0013 decision 17's ``status`` half: the listing and the view of one
task alike print on stderr, right after the paths of ADR-0014 decision
13, one ``switched off: <name> since <task> (<reason>)`` line per shared
extension the working tree's ``switches.toml`` switches off — the file
``doctor`` reads, through the same ``read_switches``, against the names
``switches.shared_extension_names`` enumerates. ``doctor`` itself now
enumerates through that one function, its output unchanged.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import agentmarshal.doctor as doctor_module
import test_doctor_extensions as doctor_helpers
import test_status_steps as status_helpers
from agentmarshal.cli import main
from agentmarshal.journal.records import read_records
from agentmarshal.switches import shared_extension_names

_OFF = """format = 1

[switches.openspec]
state = "off"
task = "CR-214"
reason = "hangs on empty repositories"
"""

_OFF_LINE = "switched off: openspec since CR-214 (hangs on empty repositories)\n"


def _off(name: str = "openspec", task: str = "CR-9", reason: str = "x") -> str:
    return (
        "format = 1\n\n"
        f"[switches.{name}]\n"
        'state = "off"\n'
        f'task = "{task}"\n'
        f'reason = "{reason}"\n'
    )


def _on(name: str = "openspec", task: str = "CR-5") -> str:
    return f'format = 1\n\n[switches.{name}]\nstate = "on"\ntask = "{task}"\n'


def _project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, switches: str | None = _OFF
) -> Path:
    repo = status_helpers._project(tmp_path, monkeypatch)
    if switches is not None:
        (repo / ".agentmarshal" / "switches.toml").write_text(
            switches, encoding="utf-8"
        )
    return repo


def _stderr(repo: Path, extra: str = "") -> str:
    return f"Placement: embedded\n{status_helpers._paths_lines(repo)}{extra}"


def test_the_listing_names_each_switched_off_extension_after_the_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the listing names each switched-off extension after the paths."""
    repo = _project(tmp_path, monkeypatch)
    doctor_helpers._dir_extension(repo)
    status_helpers._task(repo, "CR-001")

    assert main(["status"]) == 0

    captured = capsys.readouterr()
    assert captured.err == _stderr(repo, _OFF_LINE)
    assert "switched off" not in captured.out


def test_the_view_of_one_task_names_each_switched_off_extension_after_the_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the view of one task names each switched-off extension after the paths."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    doctor_helpers._dir_extension(repo)
    status_helpers._task(repo, "CR-001")

    assert main(["status", "CR-001"]) == 0

    captured = capsys.readouterr()
    assert captured.err == _stderr(repo, _OFF_LINE)


def test_the_lines_are_owed_wherever_the_paths_printed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the lines are owed wherever the paths printed — an empty journal and a failed lookup alike."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    doctor_helpers._dir_extension(repo)

    # An empty journal: the listing's "No tasks." returns early, after
    # the paths — the switched-off line stands.
    assert main(["status"]) == 0

    captured = capsys.readouterr()
    assert captured.out == "No tasks.\n"
    assert captured.err == _stderr(repo, _OFF_LINE)

    # A task the journal does not hold: the lookup's refusal comes
    # after the owed line.
    status_helpers._task(repo, "CR-001")
    assert main(["status", "CR-999"]) == 1

    captured = capsys.readouterr()
    assert captured.err.startswith(_stderr(repo, _OFF_LINE))
    assert captured.err != _stderr(repo, _OFF_LINE)


def test_a_project_without_the_file_prints_nothing_new(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a project without the file prints nothing new."""
    repo = _project(tmp_path, monkeypatch, None)
    doctor_helpers._dir_extension(repo)
    status_helpers._task(repo, "CR-001")

    assert main(["status"]) == 0
    listed = capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    detailed = capsys.readouterr()

    for captured in (listed, detailed):
        assert captured.err == _stderr(repo)


def test_a_missing_file_prints_nothing_where_the_names_cannot_be_enumerated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """No file where the names cannot be enumerated still prints nothing new.

    Absence is decided before the names are enumerated, so a managed
    path the enumeration refuses — here a symbolic link, the refusal
    ``_managed_directory`` gives — cannot produce a
    ``switches: unavailable`` line where there is no file at all.
    """
    repo = _project(tmp_path, monkeypatch, None)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (repo / ".agentmarshal" / "extensions").symlink_to(
        elsewhere, target_is_directory=True
    )
    status_helpers._task(repo, "CR-001")

    assert main(["status"]) == 0
    listed = capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    detailed = capsys.readouterr()

    for captured in (listed, detailed):
        assert captured.err == _stderr(repo)
        assert "switches" not in captured.err
    assert listed.out == "CR-001\topen\tTask\n"
    assert detailed.out.startswith("ID: CR-001\n")


def test_an_extension_switched_on_or_with_no_entry_prints_nothing_new(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extension switched on or with no entry prints nothing new."""
    repo = _project(tmp_path, monkeypatch, _on(task="CR-5"))
    doctor_helpers._dir_extension(repo, name="openspec")
    doctor_helpers._dir_extension(repo, name="zeta")
    status_helpers._task(repo, "CR-001")

    assert main(["status"]) == 0

    captured = capsys.readouterr()
    assert "switched off" not in captured.err
    assert captured.err == _stderr(repo)


def test_a_file_the_parse_refuses_is_named_on_one_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a file the parse refuses is named on one line and changes neither the exit nor stdout."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch, "this is not = toml [")
    doctor_helpers._dir_extension(repo)
    status_helpers._task(repo, "CR-001")

    assert main(["status"]) == 0

    captured = capsys.readouterr()
    assert captured.err.startswith(_stderr(repo))
    lines = [line for line in captured.err.splitlines() if "switches" in line]
    assert len(lines) == 1
    assert lines[0].startswith("switches: unavailable (")
    assert "switches.toml" in lines[0]
    assert "switched off" not in captured.err
    # Neither the exit status nor stdout changed for it.
    assert captured.out == "CR-001\topen\tTask\n"


def test_a_value_the_file_carries_is_escaped_on_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value the file carries is escaped on display."""
    repo = _project(tmp_path, monkeypatch, None)
    # A directory name carrying a newline is still an enumerated name,
    # so a switch entry can name it — and where it prints, escaped.
    (repo / ".agentmarshal" / "extensions" / "for\nmed").mkdir(parents=True)
    (repo / ".agentmarshal" / "switches.toml").write_text(
        'format = 1\n\n[switches."for\\nmed"]\n'
        'state = "off"\ntask = "CR-1"\nreason = "x"\n',
        encoding="utf-8",
    )
    status_helpers._task(repo, "CR-001")

    assert main(["status"]) == 0

    err = capsys.readouterr().err
    assert "for\nmed" not in err
    assert "switched off: for\\nmed since CR-1 (x)" in err


def test_stdout_stays_byte_for_byte_what_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: stdout stays byte for byte what it was."""
    repo = _project(tmp_path, monkeypatch)
    doctor_helpers._dir_extension(repo)
    status_helpers._task(repo, "CR-001")
    record = read_records(repo / ".agentmarshal" / "journal", "CR-001")[0]

    assert main(["status"]) == 0
    listed = capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    detailed = capsys.readouterr()

    assert listed.out == "CR-001\topen\tTask\n"
    assert detailed.out == (
        "ID: CR-001\n"
        "Status: open\n"
        "Title: Task\n"
        "Scope:\n"
        "- (none)\n"
        "Records:\n"
        f"- {record['id']} opened {record['created_at']}\n"
        "No agreement with the contract is recorded\n"
    )


def test_doctor_enumerates_through_the_shared_function(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: doctor enumerates through the shared function."""
    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)
    repo = doctor_helpers._project(tmp_path, monkeypatch)
    doctor_helpers._dir_extension(repo)
    calls: list[Path] = []
    original = shared_extension_names

    def spy(managed: Path) -> frozenset[str]:
        calls.append(managed)
        return original(managed)

    monkeypatch.setattr(doctor_module, "shared_extension_names", spy)

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    # Both enumeration sites — the checks and the report — go through it.
    managed = repo.resolve() / ".agentmarshal" / "extensions"
    assert calls == [managed, managed]
    assert "extension openspec: directory form" in captured.err


def test_a_name_declared_only_through_a_link_is_a_shared_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a name declared only through a link is a shared extension the file can switch off."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch, None)
    target = repo / "vendor" / "linked-extension"
    target.mkdir(parents=True)
    extensions = repo / ".agentmarshal" / "extensions"
    extensions.mkdir(parents=True)
    (extensions / "linked").symlink_to(target, target_is_directory=True)
    (repo / ".agentmarshal" / "switches.toml").write_text(
        _off(name="linked", task="CR-9", reason="silenced"),
        encoding="utf-8",
    )
    status_helpers._task(repo, "CR-001")

    assert main(["status"]) == 0

    captured = capsys.readouterr()
    assert captured.err == _stderr(repo, "switched off: linked since CR-9 (silenced)\n")
