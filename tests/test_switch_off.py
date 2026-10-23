"""`agentmarshal extension switch off` — the operational CR in one command.

ADR-0013 decisions 16 and 17: a shared extension is switched off only by
an operational CR, opened with one command — the task scoped to
`.agentmarshal/switches.toml` alone and the switch written for it.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

import pytest

import agentmarshal.switch_off as switch_off
import test_stages as stage_helpers
from agentmarshal.cli import main
from agentmarshal.journal.contracts import parse_contract
from agentmarshal.journal.display import escape_for_display
from agentmarshal.switches import SwitchesError, parse_switches
from test_placement import _host_and_sidecar

_REASON = "hangs on empty repositories"


def _extension(repo: Path, name: str = "openspec") -> Path:
    return stage_helpers._extension(
        repo, name=name, manifest=stage_helpers._manifest(name=name)
    )


def _file_form_extension(repo: Path, name: str = "openspec") -> Path:
    """A file-form shared extension: a single ``<name>.toml``."""

    manifest = repo / ".agentmarshal" / "extensions" / f"{name}.toml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "schema = 1\n"
        f'name = "{name}"\n'
        'version = "1.0.0"\n'
        "footprint = []\n"
        "documents = []\n"
        "artifacts = []\n"
        'install = "none"\n'
        'remove = "none"\n',
        encoding="utf-8",
    )
    return manifest


def _switches_file(repo: Path) -> Path:
    return repo / ".agentmarshal" / "switches.toml"


def _task_dirs(repo: Path) -> list[Path]:
    tasks = repo / ".agentmarshal" / "journal" / "tasks"
    return sorted(tasks.iterdir()) if tasks.is_dir() else []


def _switch_off(name: str = "openspec", reason: str = _REASON) -> int:
    return main(["extension", "switch", "off", name, "--reason", reason])


def _switches(repo: Path) -> dict[str, Any]:
    data = tomllib.loads(_switches_file(repo).read_text(encoding="utf-8"))
    return dict(data.get("switches", {}))


# -- the command opens an operational task and writes the switch ---------------


def test_the_opened_contract_names_the_extension_scopes_the_switches_file_and_accepts_the_switch_off(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the opened contract names the extension, scopes the switches file and accepts the switch-off."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)

    assert _switch_off() == 0

    (task,) = _task_dirs(repo)
    header = parse_contract(task / "contract.md")
    assert "openspec" in header.title
    assert header.scope == (".agentmarshal/switches.toml",)
    (acceptance,) = header.acceptance
    assert "openspec" in acceptance
    assert "switched off" in acceptance
    assert _REASON in acceptance


def test_the_switches_entry_is_written_for_the_opened_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the switches entry is written for the opened task."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)

    assert _switch_off() == 0

    (task,) = _task_dirs(repo)
    entry = _switches(repo)["openspec"]
    assert entry == {
        "state": "off",
        "task": task.name,
        "reason": _REASON,
    }


def test_a_missing_switches_file_is_created_with_format_and_the_switches_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a missing switches file is created with format and the switches table."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)

    assert _switch_off() == 0

    text = _switches_file(repo).read_text(encoding="utf-8")
    assert text.startswith("format = 1\n\n[switches]\n")
    data = tomllib.loads(text)
    assert data["format"] == 1
    assert data["switches"]["openspec"]["state"] == "off"


def test_the_paths_are_printed_and_nothing_is_committed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the paths are printed and nothing is committed."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    stage_helpers._commit_all(repo, "base")
    head = stage_helpers._git(repo, "rev-parse", "HEAD")
    capsys.readouterr()

    assert _switch_off() == 0

    out = capsys.readouterr().out.splitlines()
    (task,) = _task_dirs(repo)
    assert out == [
        str(task / "contract.md"),
        str(next((task / "records").iterdir())),
        str(_switches_file(repo)),
    ]
    # The command opens a task and writes a file; it never commits.
    assert stage_helpers._git(repo, "rev-parse", "HEAD") == head


# -- name, reason and the existing file are checked before the task ------------


def test_a_name_the_working_tree_does_not_declare_is_refused_before_anything_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a name the working tree does not declare is refused before anything is written."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)

    assert _switch_off(name="ghost") == 1

    captured = capsys.readouterr()
    assert "ghost" in captured.err
    assert "not a shared extension the working tree declares" in captured.err
    assert _task_dirs(repo) == []
    assert not _switches_file(repo).exists()


def test_a_reason_outside_its_rule_is_refused_before_anything_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a reason outside its rule is refused before anything is written."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)

    for reason in ("", "x" * 1001, "for\ngeable"):
        assert _switch_off(reason=reason) == 1, reason[:20]

    captured = capsys.readouterr()
    assert "reason" in captured.err
    assert _task_dirs(repo) == []
    assert not _switches_file(repo).exists()


def test_a_malformed_switches_file_is_refused_naming_it_and_nothing_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed switches file is refused naming it and nothing is written."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    _switches_file(repo).write_text("this is not = toml [", encoding="utf-8")

    assert _switch_off() == 1

    captured = capsys.readouterr()
    assert "switches.toml" in captured.err
    assert _task_dirs(repo) == []
    assert _switches_file(repo).read_text(encoding="utf-8") == "this is not = toml ["


def test_an_extension_already_switched_off_is_refused_naming_the_task_that_switched_it_off(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extension already switched off is refused naming the task that switched it off."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    _switches_file(repo).write_text(
        "format = 1\n\n[switches]\n\n"
        "[switches.openspec]\n"
        'state = "off"\n'
        'task = "CR-214"\n'
        f'reason = "{_REASON}"\n',
        encoding="utf-8",
    )

    assert _switch_off() == 1

    captured = capsys.readouterr()
    assert "CR-214" in captured.err
    assert "already" in captured.err
    assert _task_dirs(repo) == []
    assert 'task = "CR-214"' in _switches_file(repo).read_text(encoding="utf-8")


def test_a_file_form_extension_is_a_shared_extension_the_command_switches_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a file-form extension is a shared extension the command switches off."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _file_form_extension(repo)

    assert _switch_off() == 0

    assert _switches(repo)["openspec"]["state"] == "off"


# -- the file keeps its text and is replaced atomically -------------------------


def test_an_existing_on_entrys_table_is_replaced_and_the_files_other_content_is_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an existing on entry's table is replaced and the file's other content is kept."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    _extension(repo, name="zeta")
    _switches_file(repo).write_text(
        "format = 1\n"
        "\n"
        "# a comment about the file\n"
        "\n"
        "[switches]\n"
        "\n"
        "# openspec's switch — currently on\n"
        "[switches.openspec]\n"
        'state = "on"\n'
        'task = "CR-3"\n'
        "# trailing note that belongs after the table\n"
        "\n"
        "[switches.zeta]\n"
        'state = "on"\n'
        'task = "CR-9"\n',
        encoding="utf-8",
    )

    assert _switch_off() == 0

    text = _switches_file(repo).read_text(encoding="utf-8")
    (task,) = _task_dirs(repo)
    assert text == (
        "format = 1\n"
        "\n"
        "# a comment about the file\n"
        "\n"
        "[switches]\n"
        "\n"
        "# openspec's switch — currently on\n"
        "[switches.openspec]\n"
        'state = "off"\n'
        f'task = "{task.name}"\n'
        f'reason = "{_REASON}"\n'
        "# trailing note that belongs after the table\n"
        "\n"
        "[switches.zeta]\n"
        'state = "on"\n'
        'task = "CR-9"\n'
    )


def test_a_new_entry_is_appended_after_the_files_existing_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a new entry is appended after the file's existing content."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    _extension(repo, name="zeta")
    existing = 'format = 1\n\n[switches.zeta]\nstate = "on"\ntask = "CR-9"\n'
    _switches_file(repo).write_text(existing, encoding="utf-8")

    assert _switch_off() == 0

    text = _switches_file(repo).read_text(encoding="utf-8")
    (task,) = _task_dirs(repo)
    assert text == existing + (
        "\n"
        "[switches.openspec]\n"
        'state = "off"\n'
        f'task = "{task.name}"\n'
        f'reason = "{_REASON}"\n'
    )


def test_the_new_text_is_parsed_back_before_it_replaces_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the new text is parsed back before it replaces the file."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    real_parse = parse_switches
    calls = 0

    def refuse_after_open(*arguments: Any) -> Any:
        # The pre-open verification parses the rewritten text too — a
        # refusal that can only land after the task is opened is the one
        # whose line names it, so the parser fails on its second call.
        nonlocal calls
        calls += 1
        if calls > 1:
            raise SwitchesError("rewritten text does not parse")
        return real_parse(*arguments)

    monkeypatch.setattr(switch_off, "parse_switches", refuse_after_open)
    capsys.readouterr()

    assert _switch_off() == 1

    captured = capsys.readouterr()
    (task,) = _task_dirs(repo)
    failure = [
        line for line in captured.err.splitlines() if f"opened {task.name}" in line
    ]
    assert len(failure) == 1
    assert "switches.toml" in failure[0]
    assert not _switches_file(repo).exists()


def test_the_file_is_replaced_by_a_temporary_file_renamed_in_the_same_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the file is replaced by a temporary file renamed in the same directory."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    calls: list[tuple[str, str]] = []
    replace = os.replace

    def spy(
        source: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        destination: str | bytes | os.PathLike[str] | os.PathLike[bytes],
    ) -> None:
        calls.append((os.fsdecode(source), os.fsdecode(destination)))
        replace(source, destination)

    monkeypatch.setattr(os, "replace", spy)
    capsys.readouterr()

    assert _switch_off() == 0

    (call,) = calls
    staging, target = call
    assert Path(staging).parent == repo / ".agentmarshal"
    assert Path(target) == _switches_file(repo)
    # The staging file is gone: the rename published it.
    assert not Path(staging).exists()
    assert not list((repo / ".agentmarshal").glob(".switches-*.tmp"))


def test_a_failure_after_the_task_is_opened_names_the_task_on_one_line_and_exits_non_zero(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a failure after the task is opened names the task on one line and exits non-zero."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)

    def boom(
        source: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        destination: str | bytes | os.PathLike[str] | os.PathLike[bytes],
    ) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    capsys.readouterr()

    assert _switch_off() == 1

    captured = capsys.readouterr()
    (task,) = _task_dirs(repo)
    failure = [
        line for line in captured.err.splitlines() if f"opened {task.name}" in line
    ]
    assert len(failure) == 1
    assert "switches.toml" in failure[0]
    assert "disk full" in failure[0]
    # The task stands in the journal; the file was never written.
    assert not _switches_file(repo).exists()


# -- the command's surface ------------------------------------------------------


def test_the_extension_group_takes_switch_off_with_a_name_and_a_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the extension group takes switch off with a name and a reason."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)

    assert main(["extension", "switch", "off", "openspec", "--reason", _REASON]) == 0
    with pytest.raises(SystemExit):
        main(["extension", "switch", "on", "openspec"])
    with pytest.raises(SystemExit):
        main(["extension", "switch"])


def test_a_sidecar_refuses_saying_operational_tasks_are_not_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a sidecar refuses saying operational tasks are not available."""
    _host, sidecar, _base, _head = _host_and_sidecar(tmp_path, monkeypatch)
    _extension(sidecar)
    capsys.readouterr()

    assert _switch_off() == 1

    captured = capsys.readouterr()
    assert "operational tasks are not available in a sidecar" in captured.err
    assert _task_dirs(sidecar) == []
    assert not _switches_file(sidecar).exists()


def test_a_value_that_could_forge_a_line_is_escaped_on_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value that could forge a line is escaped on display."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    # A switches entry whose name carries a forgeable character: the
    # parse refuses it and quotes it, and the quoted value is shown
    # escaped — the escape, never the raw character.
    _switches_file(repo).write_text(
        'format = 1\n\n[switches."for\u2028ged"]\nstate = "on"\ntask = "CR-1"\n',
        encoding="utf-8",
    )

    assert _switch_off() == 1

    captured = capsys.readouterr()
    assert "\\u2028" in captured.err
    assert "\u2028" not in captured.err
    assert _task_dirs(repo) == []


# -- beyond the spec ------------------------------------------------------------


def test_an_on_entry_carrying_a_multi_line_nested_array_is_not_corrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An `on` entry with a multi-line nested array is rewritten or refused.

    Keys beyond state/task/reason pass unread, so the parser accepts the
    entry — but a `[`-led continuation line inside the array is where a
    line scanner can mistake the table's end. The command either replaces
    the table correctly or refuses before any task is opened; in both
    cases there is no orphan task and no corrupted file.
    """
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    original = (
        "format = 1\n\n[switches]\n\n"
        "[switches.openspec]\n"
        'state = "on"\n'
        'task = "CR-1"\n'
        "extra = [\n"
        '  ["nested", "array"],\n'
        '  ["lines"],\n'
        "]\n"
    )
    _switches_file(repo).write_text(original, encoding="utf-8")

    result = _switch_off()

    if result == 0:
        # The table was replaced correctly — the off entry reads back.
        (task,) = _task_dirs(repo)
        assert _switches(repo)["openspec"] == {
            "state": "off",
            "task": task.name,
            "reason": _REASON,
        }
    else:
        # Refused before any task was opened: the file stands as it was.
        assert result == 1
        assert "switches.toml" in capsys.readouterr().err
        assert _task_dirs(repo) == []
        assert _switches_file(repo).read_text(encoding="utf-8") == original


def test_every_path_the_command_prints_is_escaped_on_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every path the command prints is escaped — the success lines included.

    The project can sit on a path carrying a character the forgeable-text
    rule refuses: the contract, record and switches paths print escaped,
    and so does the file a refusal names.
    """
    repo = tmp_path / "rep\u2028o"
    repo.mkdir()
    stage_helpers._git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    _extension(repo)
    capsys.readouterr()

    assert _switch_off() == 0

    captured = capsys.readouterr()
    assert "\u2028" not in captured.out
    assert "\u2028" not in captured.err
    (task,) = _task_dirs(repo)
    assert captured.out.splitlines() == [
        escape_for_display(str(task / "contract.md")),
        escape_for_display(str(next((task / "records").iterdir()))),
        escape_for_display(str(_switches_file(repo))),
    ]

    # A refusal naming the file escapes it the same way.
    _switches_file(repo).write_text("not = toml [", encoding="utf-8")

    assert _switch_off() == 1

    captured = capsys.readouterr()
    assert "rep\\u2028o" in captured.err
    assert "\u2028" not in captured.err


def test_an_on_entry_with_no_table_header_is_refused_naming_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An `on` entry in a form with no `[switches.<name>]` table is refused.

    The entry parses — an inline table under `[switches]` — but there is
    no table to replace and appending a same-named one would write a
    file the parse refuses, so the refusal lands before the task is
    opened and writes nothing.
    """
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    _switches_file(repo).write_text(
        'format = 1\n\n[switches]\nopenspec = {state = "on", task = "CR-1"}\n',
        encoding="utf-8",
    )

    assert _switch_off() == 1

    captured = capsys.readouterr()
    assert "switches.toml" in captured.err
    assert "openspec" in captured.err
    assert _task_dirs(repo) == []


def test_a_reason_needing_escape_is_written_as_a_toml_basic_string(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reason with quotes or a backslash is quoted with its escapes."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    _extension(repo)
    reason = 'a "quoted" \\ reason'

    assert _switch_off(reason=reason) == 0

    entry = _switches(repo)["openspec"]
    assert entry["reason"] == reason
