"""Shared extension switches — ADR-0013 decisions 16, 17, 6 and 7.

`.agentmarshal/switches.toml` is parsed fail-closed by one function;
`stage run` reads it from the merge base's tree and reports a
switched-off extension instead of running it; `doctor` shows each
switched-off extension from the working tree.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import test_doctor_extensions as doctor_helpers
import test_stages as stage_helpers
from agentmarshal.cli import main
from agentmarshal.switches import (
    SwitchesError,
    parse_switches,
    read_switches,
)

_OFF = """format = 1

[switches.openspec]
state = "off"
task = "CR-214"
reason = "hangs on empty repositories"
"""


def _off(
    name: str = "openspec",
    task: str = "CR-214",
    reason: str = "hangs on empty repositories",
) -> str:
    return (
        "format = 1\n\n"
        f"[switches.{name}]\n"
        'state = "off"\n'
        f'task = "{task}"\n'
        f'reason = "{reason}"\n'
    )


def _on(name: str = "openspec", task: str = "CR-5") -> str:
    return f'format = 1\n\n[switches.{name}]\nstate = "on"\ntask = "{task}"\n'


def _repo_with_switches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    switches: str | None = _OFF,
    name: str = "openspec",
    manifest: str | None = None,
    files: dict[str, str] | None = None,
) -> tuple[Path, str, str]:
    """Project, extension and switches file committed on master; candidate ahead."""

    repo = stage_helpers._project(tmp_path, monkeypatch)
    stage_helpers._extension(repo, name=name, manifest=manifest, files=files)
    if switches is not None:
        (repo / ".agentmarshal" / "switches.toml").write_text(
            switches, encoding="utf-8"
        )
    base = stage_helpers._commit_all(repo, "base")
    stage_helpers._git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "candidate.txt").write_text("x\n", encoding="utf-8")
    candidate = stage_helpers._commit_all(repo, "candidate")
    return repo, base, candidate


# -- the file -----------------------------------------------------------------


def test_an_off_switch_parses_with_its_task_and_reason() -> None:
    """Scenario: an off switch parses with its task and reason."""
    switches = parse_switches(_OFF.encode("utf-8"), "switches.toml", {"openspec"})

    assert switches["openspec"].state == "off"
    assert switches["openspec"].task == "CR-214"
    assert switches["openspec"].reason == "hangs on empty repositories"


def test_a_missing_switches_file_means_every_extension_is_on(
    tmp_path: Path,
) -> None:
    """Scenario: a missing switches file means every extension is on."""
    assert read_switches(tmp_path / "switches.toml", {"openspec"}) == {}


def test_a_file_that_is_not_toml_is_refused_naming_it(tmp_path: Path) -> None:
    """Scenario: a file that is not TOML is refused naming it."""
    bad = tmp_path / "switches.toml"
    bad.write_bytes(b"this is not = toml [")

    with pytest.raises(SwitchesError) as error:
        read_switches(bad, {"openspec"})

    assert str(bad) in str(error.value)
    assert "malformed" in str(error.value)
    # The file's own entries could not be enumerated at all.
    assert error.value.names is None

    with pytest.raises(SwitchesError) as error:
        parse_switches(b"\xff\xfe binary", "blob", {"openspec"})
    assert "blob" in str(error.value)


def test_an_unknown_or_missing_format_is_refused_naming_the_file() -> None:
    """Scenario: an unknown or missing format is refused naming the file."""
    for text in (
        '[switches.openspec]\nstate = "on"\ntask = "CR-1"\n',
        'format = 2\n\n[switches.openspec]\nstate = "on"\ntask = "CR-1"\n',
        'format = "1"\n\n[switches.openspec]\nstate = "on"\ntask = "CR-1"\n',
        'format = true\n\n[switches.openspec]\nstate = "on"\ntask = "CR-1"\n',
    ):
        with pytest.raises(SwitchesError) as error:
            parse_switches(text.encode("utf-8"), "the-file", {"openspec"})
        assert "the-file" in str(error.value)
        assert "format" in str(error.value)


def test_a_file_without_a_switches_table_is_refused_naming_it() -> None:
    """A file carrying no `[switches]` table is refused; an empty one is all-on."""
    for text in (
        "format = 1\n",
        "format = 1\n\n[grants.openspec]\nfiles = {}\n",
    ):
        with pytest.raises(SwitchesError) as error:
            parse_switches(text.encode("utf-8"), "the-file", {"openspec"})
        assert "the-file: missing 'switches'" in str(error.value)
        # No table, no keys to enumerate: the file could have named
        # anything, so no entry names are declared.
        assert error.value.names is None

    assert parse_switches(b"format = 1\n\n[switches]\n", "the-file", {"openspec"}) == {}


def test_an_entry_naming_no_shared_extension_is_refused_naming_the_file_and_the_entry() -> (  # noqa: E501
    None
):
    """Scenario: an entry naming no shared extension is refused naming the file and the entry."""  # noqa: E501
    with pytest.raises(SwitchesError) as error:
        parse_switches(_OFF.encode("utf-8"), "the-file", {"other"})

    assert "the-file" in str(error.value)
    assert "'openspec'" in str(error.value)
    assert "no shared extension" in str(error.value)
    assert error.value.names == frozenset({"openspec"})


def test_a_switch_entry_outside_its_shape_is_refused_naming_the_file_and_the_entry() -> (  # noqa: E501
    None
):
    """Scenario: a switch entry outside its shape is refused naming the file and the entry."""  # noqa: E501
    bodies = [
        "[switches.openspec]\n",  # missing every field
        '[switches]\nopenspec = "off"\n',  # a bare value, not a table
        '[switches.openspec]\nstate = "sideways"\ntask = "CR-1"\n',
        '[switches.openspec]\nstate = "off"\ntask = "not-a-task"\nreason = "x"\n',
        '[switches.openspec]\nstate = "off"\ntask = "CR-1"\n',  # off, no reason
        '[switches.openspec]\nstate = "off"\ntask = "CR-1"\nreason = ""\n',
        '[switches.openspec]\nstate = "on"\ntask = "CR-1"\nreason = "x"\n',
        '[switches.openspec]\nstate = "off"\ntask = "CR-1"\nreason = "'
        + "x" * 1001
        + '"\n',
        '[switches.openspec]\nstate = "off"\ntask = "CR-1"\nreason = "for\\nged"\n',
    ]
    for body in bodies:
        text = f"format = 1\n\n{body}"
        with pytest.raises(SwitchesError) as error:
            parse_switches(text.encode("utf-8"), "the-file", {"openspec"})
        assert "the-file" in str(error.value)
        assert "'openspec'" in str(error.value), body


# -- stage run -----------------------------------------------------------------


def test_a_switched_off_extension_prints_switched_off_task_reason_and_does_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a switched-off extension prints switched off (task, reason) and does not run."""  # noqa: E501
    _repo_with_switches(tmp_path, monkeypatch)
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec: switched off (CR-214, hangs on empty repositories)" in out
    # Nothing of the extension ran: no output frame, no materialization.
    assert "openspec | " not in out
    assert "check ran" not in out


def test_the_switches_are_read_from_the_base_commit_never_the_candidate_or_the_working_tree(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the switches are read from the base commit, never the candidate or the working tree."""  # noqa: E501
    repo, _base, _candidate = _repo_with_switches(tmp_path, monkeypatch)
    switches_file = repo / ".agentmarshal" / "switches.toml"
    # The candidate switches the extension back on; the working tree
    # removes the file outright. The base's switch-off still decides.
    switches_file.write_text(_on(task="CR-999"), encoding="utf-8")
    stage_helpers._commit_all(repo, "candidate switches it on")
    switches_file.unlink()
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec: switched off (CR-214, hangs on empty repositories)" in out
    assert "check ran" not in out


def test_the_switches_are_read_from_the_base_commit_never_the_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the switches are read from the base commit, never the candidate or the working tree."""  # noqa: E501
    repo, _base, _candidate = _repo_with_switches(tmp_path, monkeypatch, switches=None)
    # The other direction: the base carries no file, the candidate
    # switches the extension off — the run still runs it.
    (repo / ".agentmarshal" / "switches.toml").write_text(_OFF, encoding="utf-8")
    stage_helpers._commit_all(repo, "candidate switches it off")
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | check ran" in out
    assert "openspec: checked" in out
    assert "switched off" not in out


def test_a_switched_off_pre_gate_stop_stage_does_not_pause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a switched-off pre-gate-stop stage does not pause."""
    _repo_with_switches(tmp_path, monkeypatch)
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "paused" not in captured.err
    assert "openspec: switched off" in captured.out


def test_every_stage_of_a_switched_off_extension_gets_the_switched_off_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every stage of a switched-off extension gets the switched-off line."""
    _repo_with_switches(
        tmp_path,
        monkeypatch,
        manifest=stage_helpers._manifest(
            stages=(
                ("pre-gate-stop", "bin/one.py"),
                ("pre-gate-stop", "bin/two.py"),
            )
        ),
        files={"bin/one.py": "print('one')\n", "bin/two.py": "print('two')\n"},
    )
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert out.count("openspec: switched off (CR-214,") == 2
    # No output frame ever appeared: no stage process ran.
    assert "openspec | " not in out


def test_a_switched_off_stages_event_carries_the_switched_off_decision_the_task_and_the_reason(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a switched-off stage's event carries the switched-off decision, the task and the reason."""  # noqa: E501
    repo, _base, candidate = _repo_with_switches(tmp_path, monkeypatch)
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 0

    events = [
        event
        for event in stage_helpers._events(repo)
        if event["event"] == "extension-event"
    ]
    (event,) = events
    assert event["extension"] == "openspec"
    assert event["scope"] == "shared"
    assert event["phase"] == "pre-gate-stop"
    assert event["decision"] == "switched-off"
    assert event["reason"] == "CR-214, hangs on empty repositories"
    assert event["commit"] == candidate
    assert event["task"] == "CR-001"


def test_an_extension_switched_on_or_with_no_entry_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extension switched on or with no entry runs."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    stage_helpers._extension(
        repo,
        name="openspec",
        files={"bin/check.py": "print('o')\n"},
    )
    stage_helpers._extension(
        repo,
        name="zeta",
        manifest=stage_helpers._manifest(name="zeta"),
        files={"bin/check.py": "print('z')\n"},
    )
    (repo / ".agentmarshal" / "switches.toml").write_text(
        _on(task="CR-5"), encoding="utf-8"
    )
    stage_helpers._commit_all(repo, "base")
    stage_helpers._git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    stage_helpers._commit_all(repo, "candidate")
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec: checked" in out
    assert "zeta: checked" in out
    assert "switched off" not in out


def test_a_malformed_switches_file_is_reported_on_one_line_and_no_stage_of_an_extension_it_names_runs(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed switches file is reported on one line and no stage of an extension it names runs."""  # noqa: E501
    repo = stage_helpers._project(tmp_path, monkeypatch)
    stage_helpers._extension(repo, name="openspec")
    stage_helpers._extension(
        repo,
        name="zeta",
        manifest=stage_helpers._manifest(name="zeta"),
        files={"bin/check.py": "print('z')\n"},
    )
    # openspec's entry is outside its shape; beta's is well-formed — but
    # the file names both, so neither runs. zeta, unnamed, still runs.
    (repo / ".agentmarshal" / "switches.toml").write_text(
        "format = 1\n\n"
        "[switches.openspec]\n"
        'state = "sideways"\n'
        'task = "CR-1"\n\n'
        "[switches.beta]\n"
        'state = "on"\n'
        'task = "CR-1"\n',
        encoding="utf-8",
    )
    stage_helpers._extension(
        repo,
        name="beta",
        manifest=stage_helpers._manifest(name="beta"),
        files={"bin/check.py": "print('b')\n"},
    )
    stage_helpers._commit_all(repo, "base")
    stage_helpers._git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    stage_helpers._commit_all(repo, "candidate")
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    # The refusal is reported once, naming the file and the entry.
    malformed = [line for line in captured.err.splitlines() if "switches.toml" in line]
    assert len(malformed) == 1
    assert "'openspec'" in malformed[0]
    assert "state" in malformed[0]
    assert "beta: not run (shared switches file unreadable)" in captured.out
    assert "openspec: not run (shared switches file unreadable)" in captured.out
    assert "zeta: checked" in captured.out
    assert "openspec | " not in captured.out


def test_a_switches_file_that_cannot_be_read_leaves_every_stage_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a switches file that cannot be read leaves every stage not run."""
    _repo_with_switches(tmp_path, monkeypatch, switches="this is not = toml [")
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    malformed = [line for line in captured.err.splitlines() if "switches.toml" in line]
    assert len(malformed) == 1
    assert "malformed" in malformed[0]
    assert "openspec: not run (shared switches file unreadable)" in captured.out
    assert "paused before the gate" in captured.err


def test_a_malformed_trust_file_still_reports_the_switched_off_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed trust.toml fails the command naming it."""
    # Extended: a switched-off stage is never grant-checked, so a trust
    # file the run cannot read does not suppress its result line — the
    # command still fails naming the file, once the owed line is printed.
    repo = stage_helpers._project(tmp_path, monkeypatch)
    stage_helpers._extension(repo, name="openspec")
    stage_helpers._extension(
        repo,
        name="zeta",
        manifest=stage_helpers._manifest(name="zeta"),
        files={"bin/check.py": "print('z')\n"},
    )
    (repo / ".agentmarshal" / "switches.toml").write_text(
        "format = 1\n\n"
        "[switches.openspec]\n"
        'state = "off"\n'
        'task = "CR-214"\n'
        'reason = "hangs on empty repositories"\n\n'
        "[switches.zeta]\n"
        'state = "on"\n'
        'task = "CR-9"\n',
        encoding="utf-8",
    )
    stage_helpers._commit_all(repo, "base")
    stage_helpers._git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    stage_helpers._commit_all(repo, "candidate")
    trust_file = repo / ".git" / "agentmarshal" / "trust.toml"
    trust_file.parent.mkdir(parents=True, exist_ok=True)
    trust_file.write_text("this is not toml [", encoding="utf-8")
    stage_helpers._workstation(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 1

    captured = capsys.readouterr()
    trust = [line for line in captured.err.splitlines() if "trust.toml" in line]
    assert len(trust) == 1
    assert "openspec: switched off (CR-214, hangs on empty repositories)" in (
        captured.out
    )
    # The switched-on extension's stage neither ran nor reported a line.
    assert "zeta" not in captured.out
    events = [
        event
        for event in stage_helpers._events(repo)
        if event["event"] == "extension-event"
    ]
    (event,) = events
    assert event["extension"] == "openspec"
    assert event["decision"] == "switched-off"
    assert event["reason"] == "CR-214, hangs on empty repositories"


def test_a_malformed_switches_file_and_trust_file_still_report_the_named_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Both files unreadable: the switches-blocked lines are still owed.

    With the base's switches file and the clone's trust file each
    unreadable, a stage of an extension the switches file names prints
    its `not run (shared switches file unreadable)` line — it was never
    going to be grant-checked — while a stage the file does not name,
    which would have needed a grant, is skipped silently; each refusal
    keeps its one stderr line and the exit is 1.
    """
    repo = stage_helpers._project(tmp_path, monkeypatch)
    stage_helpers._extension(repo, name="openspec")
    stage_helpers._extension(
        repo,
        name="zeta",
        manifest=stage_helpers._manifest(name="zeta"),
        files={"bin/check.py": "print('z')\n"},
    )
    # openspec's entry is outside its shape but the TOML parses, so the
    # file's names enumerate — to openspec alone.
    (repo / ".agentmarshal" / "switches.toml").write_text(
        'format = 1\n\n[switches.openspec]\nstate = "sideways"\ntask = "CR-1"\n',
        encoding="utf-8",
    )
    stage_helpers._commit_all(repo, "base")
    stage_helpers._git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    stage_helpers._commit_all(repo, "candidate")
    trust_file = repo / ".git" / "agentmarshal" / "trust.toml"
    trust_file.parent.mkdir(parents=True, exist_ok=True)
    trust_file.write_text("this is not toml [", encoding="utf-8")
    stage_helpers._workstation(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="candidate", base="master") == 1

    captured = capsys.readouterr()
    trust = [line for line in captured.err.splitlines() if "trust.toml" in line]
    assert len(trust) == 1
    switches = [line for line in captured.err.splitlines() if "switches.toml" in line]
    assert len(switches) == 1
    assert "'openspec'" in switches[0]
    assert "openspec: not run (shared switches file unreadable)" in captured.out
    # The extension the file does not name would have needed a grant:
    # skipped silently — no result line, no output frame, no event.
    assert "zeta" not in captured.out
    events = [
        event
        for event in stage_helpers._events(repo)
        if event["event"] == "extension-event"
    ]
    (event,) = events
    assert event["extension"] == "openspec"
    assert event["decision"] == "not-run"
    assert event["reason"] == "shared switches file unreadable"


def test_a_malformed_switches_file_is_reported_even_with_no_stage_in_the_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed switches file is reported on one line and no stage of an extension it names runs."""  # noqa: E501
    # Extended: the base's file is read before the empty-plan return, so
    # its refusal prints even where the requested phase declares no
    # stage — then the no-stage line and exit 0, nothing having been
    # blocked because nothing would have run.
    repo = stage_helpers._project(tmp_path, monkeypatch)
    stage_helpers._extension(repo, name="openspec")  # a pre-gate-stop stage only
    (repo / ".agentmarshal" / "switches.toml").write_text(
        "this is not = toml [", encoding="utf-8"
    )
    stage_helpers._commit_all(repo, "base")
    stage_helpers._git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    stage_helpers._commit_all(repo, "candidate")
    stage_helpers._ci(monkeypatch)
    capsys.readouterr()

    assert (
        stage_helpers._stage_run(phase="post-gate", commit="candidate", base="master")
        == 0
    )

    captured = capsys.readouterr()
    malformed = [line for line in captured.err.splitlines() if "switches.toml" in line]
    assert len(malformed) == 1
    assert "malformed" in malformed[0]
    assert "no shared extension declares a post-gate stage" in captured.out


# -- doctor --------------------------------------------------------------------


def _doctor_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, switches: str | None = None
) -> Path:
    repo = doctor_helpers._project(tmp_path, monkeypatch)
    if switches is not None:
        (repo / ".agentmarshal" / "switches.toml").write_text(
            switches, encoding="utf-8"
        )
    return repo


def test_doctor_shows_a_switched_off_extension_with_its_task_and_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: doctor shows a switched-off extension with its task and reason."""
    repo = _doctor_repo(tmp_path, monkeypatch, _OFF)
    doctor_helpers._dir_extension(repo)

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    assert "extension openspec:" in err
    assert "switched off since CR-214 (hangs on empty repositories)" in err


def test_a_project_without_switches_toml_shows_nothing_new(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a project without switches.toml shows nothing new."""
    repo = _doctor_repo(tmp_path, monkeypatch)
    doctor_helpers._dir_extension(repo)

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    assert "switched off" not in err
    assert "switches" not in err
    assert "extension openspec: directory form" in err


def test_an_extension_switched_on_or_with_no_entry_shows_no_switch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extension switched on or with no entry shows no switch."""
    repo = _doctor_repo(tmp_path, monkeypatch, _on(task="CR-5"))
    doctor_helpers._dir_extension(repo, name="openspec")
    doctor_helpers._dir_extension(repo, name="zeta")

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    assert "switched off" not in err
    assert "extension openspec:" in err
    assert "extension zeta:" in err


def test_a_file_form_extension_switched_off_is_shown_the_same_way(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a file-form extension switched off is shown the same way."""
    repo = _doctor_repo(tmp_path, monkeypatch, _off(name="declared"))
    doctor_helpers._file_extension(repo)

    assert main(["doctor"]) == 0

    err = capsys.readouterr().err
    line = next(
        line for line in err.splitlines() if line.startswith("extension declared:")
    )
    assert "file form" in line
    assert "switched off since CR-214 (hangs on empty repositories)" in line


def test_a_malformed_switches_file_is_named_on_one_line_and_fails_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed switches file is named on one line and fails nothing."""
    repo = _doctor_repo(tmp_path, monkeypatch, "this is not = toml [")
    doctor_helpers._every_precondition_met(repo, monkeypatch)
    doctor_helpers._dir_extension(repo)

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    lines = [line for line in captured.err.splitlines() if line.startswith("switches:")]
    assert len(lines) == 1
    assert "switches: unavailable (" in lines[0]
    assert "switches.toml" in lines[0]
    assert "switched off" not in captured.err
    assert "Summary: all 11 checks passed" in captured.out


def test_a_value_that_could_forge_a_line_is_escaped_on_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value that could forge a line is escaped on display."""
    repo = _doctor_repo(tmp_path, monkeypatch)
    # A directory name carrying a newline is still a discovered name, so
    # a switch entry can name it — and where it prints, it prints escaped.
    (repo / ".agentmarshal" / "extensions" / "for\nmed").mkdir(parents=True)
    (repo / ".agentmarshal" / "switches.toml").write_text(
        'format = 1\n\n[switches."for\\nmed"]\n'
        'state = "off"\ntask = "CR-1"\nreason = "x"\n',
        encoding="utf-8",
    )

    assert main(["doctor"]) == 1

    err = capsys.readouterr().err
    assert "for\nmed" not in err
    assert "extension for\\nmed:" in err
    assert "switched off since CR-1 (x)" in err
