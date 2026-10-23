"""The operational lane of the gate (ADR-0013 decision 17).

A candidate whose diff touches only ``.agentmarshal/switches.toml`` and
its own task's journal records — opened under a contract declaring
exactly that file as scope — is admitted without a review, and
``stage run --phase pre-gate`` runs nothing for it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.contracts import contract_sha256
from agentmarshal.journal.gate import run_gate
from agentmarshal.journal.records import (
    create_opened_record,
    create_session_record,
    write_record,
)
from test_gate import _commit_all, _run, _write_extension_manifest
from test_placement import _host_and_sidecar
from test_stages import _ci, _events, _extension, _manifest, _project, _stage_run

_SWITCHES = ".agentmarshal/switches.toml"
_OFF_CR_001 = (
    'format = 1\n\n[switches.openspec]\nstate = "off"\n'
    'task = "CR-001"\nreason = "its stage hangs"\n'
)


def _operational_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, str]:
    """Repo with a file-form extension and a switches-scoped task at base."""

    repo = _project(tmp_path, monkeypatch)
    _write_extension_manifest(repo)
    assert main(["open", "--title", "Switch off openspec", "--scope", _SWITCHES]) == 0
    base = _commit_all(repo, "extension and task")
    return repo, base


def _write_switches(repo: Path, text: str | None) -> None:
    path = repo / _SWITCHES
    if text is None:
        path.unlink()
    else:
        path.write_text(text, encoding="utf-8")


def test_the_operational_lane_admits_a_switches_only_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the operational lane admits a switches-only candidate."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(repo, _OFF_CR_001)
    write_record(
        repo / ".agentmarshal" / "journal",
        "CR-001",
        create_session_record(
            "CR-001", "1.0", "implementer", "impl", "implementation", "done", 1, 2, 3
        ),
    )
    head = _commit_all(repo, "switch off openspec")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert output == (
        "PASS: task CR-001 is not closed at base\n"
        "PASS: operational transaction (operational lane; review not required)\n"
        "PASS: scope (operational lane: the diff is "
        ".agentmarshal/switches.toml and the task's own records)\n"
        "PASS: the switches file outside its entries matches the base\n"
        "PASS: every added or changed switch entry names CR-001\n"
        "NOT EXAMINED: agreement (the operational lane requires none)\n"
        "NOT EXAMINED: latest review (the operational lane requires none)\n"
        "NOT EXAMINED: reviewer independence (the operational lane requires none)\n"
        f"PASS: pipeline attested for {head[:12]}\n"
        "PASS: evidence records are append-only\n"
        "PASS: added records are valid\n"
        "PASS: no record-path collisions with the base tree\n"
        "PASS: task lifecycle records are consistent"
    ), output


def test_the_contract_is_read_from_the_base_when_the_task_exists_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the contract is read from the base when the task exists there.

    A candidate may amend its own contract inside its journal subtree;
    the lane already bounds the diff, so the base's contract decides —
    the amended contract governs the next transaction, not this one.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(f'"{_SWITCHES}"', '"src/"'),
        encoding="utf-8",
    )
    _write_switches(repo, _OFF_CR_001)
    head = _commit_all(repo, "switch off and amend")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "PASS: operational transaction" in output


def test_a_task_opened_within_the_candidate_reads_the_candidate_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a task opened within the candidate reads the candidate's contract."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    task_dir = repo / ".agentmarshal" / "journal" / "tasks" / "CR-002"
    (task_dir / "records").mkdir(parents=True)
    contract_text = (
        "+++\n"
        "schema = 2\n"
        'id = "CR-002"\n'
        'title = "Switch off openspec"\n'
        f'scope = ["{_SWITCHES}"]\n'
        "acceptance = []\n"
        "+++\n\nBody.\n"
    )
    (task_dir / "contract.md").write_text(contract_text, encoding="utf-8")
    write_record(
        repo / ".agentmarshal" / "journal",
        "CR-002",
        create_opened_record(
            "CR-002",
            "1.0",
            contract=contract_sha256(
                contract_text.encode("utf-8"), "candidate contract"
            ),
        ),
    )
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-002"\nreason = "its stage hangs"\n',
    )
    head = _commit_all(repo, "open CR-002 and switch off openspec")

    report = run_gate(repo, "CR-002", head, base, head)
    output = "\n".join(report.lines)

    assert report.passed, output
    assert "PASS: task CR-002 is not closed at base" in output
    assert "PASS: operational transaction" in output
    assert "every added or changed switch entry names CR-002" in output


def test_a_contract_declaring_another_scope_does_not_take_the_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a contract declaring another scope does not take the lane."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(f'"{_SWITCHES}"', '"src/"'),
        encoding="utf-8",
    )
    base = _commit_all(repo, "widen the scope at base")
    _write_switches(repo, _OFF_CR_001)
    head = _commit_all(repo, "switch off openspec")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "operational" not in output
    assert "FAIL: paths outside contract scope" in output
    assert "no review record" in output


def test_an_extra_path_in_the_diff_takes_the_lane_it_takes_today(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an extra path in the diff takes the lane it takes today."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(repo, _OFF_CR_001)
    (repo / "code.py").write_text("code\n", encoding="utf-8")
    head = _commit_all(repo, "switch off plus code")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "operational" not in output
    assert "FAIL: paths outside contract scope" in output
    assert "no review record" in output


def test_in_a_sidecar_the_operational_lane_is_not_offered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: in a sidecar the operational lane is not offered."""

    host, _sidecar, base, _head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Switch off", "--scope", _SWITCHES]) == 0
    writer = ["-c", "user.name=T", "-c", "user.email=t@t.invalid"]
    # Revert the helper's app.txt change so the host's diff is exactly the
    # lane's shape: the switches file plus the task's own records.
    (host / "app.txt").write_text("one\n", encoding="utf-8")
    (host / ".agentmarshal").mkdir()
    (host / _SWITCHES).write_text(_OFF_CR_001, encoding="utf-8")
    records = host / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    records.mkdir(parents=True)
    (records / "x.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=host, check=True)
    subprocess.run(
        [*["git"], *writer, "commit", "--quiet", "-m", "operational-looking"],
        cwd=host,
        check=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=host,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    capsys.readouterr()

    monkeypatch.setenv("AGENTMARSHAL_PIPELINE_OK_SHA", head)
    assert main(["gate", "--task", "CR-001", "--commit", head, "--base", base]) == 1

    captured = capsys.readouterr()
    assert "operational" not in captured.out
    assert "paths outside contract scope" in captured.out
    assert "no review record" in captured.out


def test_a_malformed_switches_file_at_the_candidate_refuses_naming_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a malformed switches file at the candidate refuses naming the file."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(repo, "format = 1\n\n[switches\n")
    head = _commit_all(repo, "malformed switches")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "PASS: operational transaction" in output
    assert f"FAIL: {head}:{_SWITCHES}: malformed:" in output


def test_an_undeclared_extension_entry_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an undeclared extension entry is refused naming file and entry."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(
        repo,
        'format = 1\n\n[switches.nosuch]\nstate = "off"\n'
        'task = "CR-001"\nreason = "not real"\n',
    )
    head = _commit_all(repo, "unknown extension")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        f"FAIL: {head}:{_SWITCHES}: malformed: switch 'nosuch' "
        "names no shared extension"
    ) in output


def test_an_entry_naming_another_task_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an entry naming another task is refused naming file and entry."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "its stage hangs"\n',
    )
    head = _commit_all(repo, "another task's switch")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        f"FAIL: {head}:{_SWITCHES}: switch entries naming another task: "
        "'openspec' (task CR-214)"
    ) in output


def test_a_removed_entry_is_refused_naming_the_file_and_the_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a removed entry is refused naming the file and the entry.

    The base's file switches openspec off under CR-214; the candidate
    drops the entry — and, in a second run, deletes the file, dropping
    every entry the base held — and each is refused naming the file and
    the entry: removing is a change like any other, so it carries the
    task that made it or it does not happen.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "dropped by CR-001"\n',
    )
    base = _commit_all(repo, "switched off at base")

    _write_switches(repo, "format = 1\n\n[switches]\n")
    head = _commit_all(repo, "drop the entry")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert f"FAIL: {head}:{_SWITCHES}: switch entries removed: 'openspec'" in output

    _write_switches(repo, None)
    head = _commit_all(repo, "delete the file")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert f"FAIL: {head}:{_SWITCHES}: switch entries removed: 'openspec'" in output


def test_a_base_file_that_cannot_be_read_keeps_the_candidate_off_the_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a base file that cannot be read keeps the candidate off the lane.

    Two base shapes — bytes that are not TOML at all, and a well-formed
    file whose entry is outside the parser's shape — each keep an
    otherwise-operational candidate on the regular lane, which needs a
    review: a removal or an unchanged entry cannot be judged against a
    base that cannot be read. ``stage run --phase pre-gate`` on the same
    candidate does not print the operational line; the stage it would
    have skipped is blocked by the unreadable base file and pauses the
    transaction, as it does on any other candidate today.
    """

    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    assert main(["open", "--title", "Switch off openspec", "--scope", _SWITCHES]) == 0
    base = _commit_all(repo, "extension and task")
    for bad_text in (
        "not toml [[[\n",
        'format = 1\n\n[switches.openspec]\nstate = "off"\n',
    ):
        _write_switches(repo, bad_text)
        base = _commit_all(repo, "unreadable switches at base")
        _write_switches(repo, _OFF_CR_001)
        head = _commit_all(repo, "switch off openspec")
        capsys.readouterr()

        passed, output = _run(repo, head, base, head)

        assert not passed
        assert "operational" not in output
        assert "no review record" in output

        assert _stage_run(commit=head, base=base) == 3
        captured = capsys.readouterr()
        assert "pre-gate stages do not run on an operational change" not in captured.out
        assert f"{base}:{_SWITCHES}" in captured.err


def test_switching_an_extension_back_on_names_this_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: switching an extension back on names this task.

    The base's file switches openspec off under CR-214; the candidate
    turns it back on — `state = "on"` carrying this task — and is
    admitted: an `on` entry is an added-or-changed entry like any
    other, naming the task that made it.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "switched off before"\n',
    )
    base = _commit_all(repo, "switched off at base")
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "on"\ntask = "CR-001"\n',
    )
    head = _commit_all(repo, "switch openspec back on")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "PASS: every added or changed switch entry names CR-001" in output


def test_an_unchanged_entry_naming_another_task_is_not_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an unchanged entry naming another task is not refused."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    (repo / ".agentmarshal" / "extensions" / "alpha.toml").write_text(
        "schema = 1\n"
        'name = "alpha"\n'
        'version = "1"\n'
        'footprint = ["alpha/"]\n'
        "documents = []\n"
        "artifacts = []\n"
        'install = "install"\n'
        'remove = "remove"\n',
        encoding="utf-8",
    )
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "switched off before"\n',
    )
    base = _commit_all(repo, "alpha and a foreign switch")
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "switched off before"\n\n'
        '[switches.alpha]\nstate = "off"\n'
        'task = "CR-001"\nreason = "its stage hangs"\n',
    )
    head = _commit_all(repo, "add alpha's switch")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "every added or changed switch entry names CR-001" in output


def test_a_change_outside_the_parsed_fields_is_still_a_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a change outside the parsed fields is still a change.

    The base's file switches openspec off under CR-214 carrying an
    extra key the parser keeps but does not read; the candidate edits
    only that key — the parsed `Switch` is identical — and is refused
    naming the file and the entry, because the lane compares the raw
    TOML tables. A candidate that instead edits a top-level key outside
    `switches` is refused naming the file.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "switched off before"\nnote = "first"\n',
    )
    base = _commit_all(repo, "switched off at base with a note")
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "switched off before"\nnote = "second"\n',
    )
    head = _commit_all(repo, "edit only the extra key")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        f"FAIL: {head}:{_SWITCHES}: switch entries naming another task: "
        "'openspec' (task CR-214)"
    ) in output

    _write_switches(
        repo,
        'format = 1\ncomment = "a top-level key"\n\n[switches.openspec]\n'
        'state = "off"\ntask = "CR-214"\nreason = "switched off before"\n'
        'note = "first"\n',
    )
    head = _commit_all(repo, "add a top-level key")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        f"FAIL: {head}:{_SWITCHES}: top-level keys differ from the base: 'comment'"
    ) in output


def test_an_extra_key_on_an_entry_naming_this_task_is_not_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An extra-key change on this task's own entry passes.

    The raw-table rule cuts the other way as well: the candidate edits
    the extra key the base's entry carries and names this task — a
    changed entry like any other, admitted.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "switched off before"\nnote = "first"\n',
    )
    base = _commit_all(repo, "switched off at base with a note")
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-001"\nreason = "switched off before"\nnote = "second"\n',
    )
    head = _commit_all(repo, "edit the extra key under this task")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "PASS: every added or changed switch entry names CR-001" in output


def test_a_type_only_change_in_another_tasks_entry_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A change of a value's type alone is a change all the same.

    Python's ``==`` reads ``1 == 1.0`` and ``True == 1`` — bool is a
    subclass of int — so a raw-table comparison by plain equality would
    see no change where TOML saw one, and an entry staying under another
    task's name would go unattributed. The lane compares a type-strict
    canonical form instead: each type move below is a changed entry, and
    an entry naming another task refuses naming the file and the entry;
    the same move on a top-level key outside ``switches`` refuses naming
    the file.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    for old, new in (("1", "1.0"), ("true", "1")):
        _write_switches(
            repo,
            'format = 1\n\n[switches.openspec]\nstate = "off"\n'
            'task = "CR-214"\nreason = "switched off before"\n'
            f"note = {old}\n",
        )
        base = _commit_all(repo, "switched off at base with a note")
        _write_switches(
            repo,
            'format = 1\n\n[switches.openspec]\nstate = "off"\n'
            'task = "CR-214"\nreason = "switched off before"\n'
            f"note = {new}\n",
        )
        head = _commit_all(repo, "move the note's type")

        passed, output = _run(repo, head, base, head)

        assert not passed
        assert (
            f"FAIL: {head}:{_SWITCHES}: switch entries naming another task: "
            "'openspec' (task CR-214)"
        ) in output

    _write_switches(repo, "format = 1\ncount = 1\n\n[switches]\n")
    base = _commit_all(repo, "a top-level key at base")
    _write_switches(repo, "format = 1\ncount = 1.0\n\n[switches]\n")
    head = _commit_all(repo, "move the top-level key's type")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        f"FAIL: {head}:{_SWITCHES}: top-level keys differ from the base: 'count'"
    ) in output


def test_a_type_only_change_in_this_tasks_entry_is_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same type-only changes are admitted when the entry names this task.

    The canonical comparison marks the entry changed; a changed entry
    naming this task in `task` is admitted, as every added or changed
    entry is.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    for old, new in (("1", "1.0"), ("true", "1")):
        _write_switches(
            repo,
            'format = 1\n\n[switches.openspec]\nstate = "off"\n'
            'task = "CR-001"\nreason = "switched off before"\n'
            f"note = {old}\n",
        )
        base = _commit_all(repo, "switched off at base with a note")
        _write_switches(
            repo,
            'format = 1\n\n[switches.openspec]\nstate = "off"\n'
            'task = "CR-001"\nreason = "switched off before"\n'
            f"note = {new}\n",
        )
        head = _commit_all(repo, "move the note's type under this task")

        passed, output = _run(repo, head, base, head)

        assert passed, output
        assert "PASS: every added or changed switch entry names CR-001" in output


def test_a_value_that_could_forge_a_line_is_escaped_on_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a value that could forge a line is escaped on display."""

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(
        repo,
        'format = 1\n\n[switches."evil\\nname"]\nstate = "off"\n'
        'task = "CR-001"\nreason = "not real"\n',
    )
    head = _commit_all(repo, "forgeable entry name")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "evil\\nname" in output
    assert "evil\nname" not in output


def test_pre_gate_stages_do_not_run_on_an_operational_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: pre-gate stages do not run on an operational change.

    The switched-off extension's pre-gate-stop stage would pause the
    transaction; on the operational candidate it never starts — the
    gate's own predicate decides before any manifest is read.
    """

    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        files={"bin/check.py": "import sys\nprint('stop ran')\nsys.exit(1)\n"},
    )
    assert main(["open", "--title", "Switch off openspec", "--scope", _SWITCHES]) == 0
    base = _commit_all(repo, "extension and task")
    _write_switches(repo, _OFF_CR_001)
    candidate = _commit_all(repo, "switch off openspec")
    capsys.readouterr()

    assert _stage_run(commit=candidate, base=base) == 0

    captured = capsys.readouterr()
    assert (
        captured.out
        == "stage run: pre-gate stages do not run on an operational change\n"
    )
    assert captured.err == ""
    assert "stop ran" not in captured.out
    assert [
        event for event in _events(repo) if event["event"] == "extension-event"
    ] == []


def test_an_operational_change_reports_no_switched_off_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an operational change reports no switched-off stage.

    The base's file already switches openspec off; the candidate switches
    it back on under this task. On the lane the pre-gate invocation plans
    no stage at all, so no `switched off` result line exists — the one
    line printed is the operational skip.
    """

    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        files={"bin/check.py": "import sys\nprint('stop ran')\nsys.exit(1)\n"},
    )
    assert main(["open", "--title", "Switch off openspec", "--scope", _SWITCHES]) == 0
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "off"\n'
        'task = "CR-214"\nreason = "switched off before"\n',
    )
    base = _commit_all(repo, "extension, task and a switched-off base")
    _write_switches(
        repo,
        'format = 1\n\n[switches.openspec]\nstate = "on"\ntask = "CR-001"\n',
    )
    candidate = _commit_all(repo, "switch openspec back on")
    capsys.readouterr()

    assert _stage_run(commit=candidate, base=base) == 0

    captured = capsys.readouterr()
    assert (
        captured.out
        == "stage run: pre-gate stages do not run on an operational change\n"
    )
    assert "switched off" not in captured.out
    assert captured.err == ""
    assert [
        event for event in _events(repo) if event["event"] == "extension-event"
    ] == []


def test_a_broken_extension_cannot_block_the_operational_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A malformed manifest is not even read on the operational candidate.

    Decision 17's point: deciding to drop an extension cannot depend on
    that extension still working — the skip precedes the manifest read
    that would otherwise fail the run.
    """

    repo = _project(tmp_path, monkeypatch)
    _extension(repo, manifest="not a manifest [[[\n")
    assert main(["open", "--title", "Switch off openspec", "--scope", _SWITCHES]) == 0
    base = _commit_all(repo, "broken extension and task")
    _write_switches(repo, _OFF_CR_001)
    candidate = _commit_all(repo, "switch off openspec")
    capsys.readouterr()

    assert _stage_run(commit=candidate, base=base) == 0

    captured = capsys.readouterr()
    assert (
        captured.out
        == "stage run: pre-gate stages do not run on an operational change\n"
    )


def test_other_phases_and_other_candidates_behave_as_today(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: other phases and other candidates behave as today."""

    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        manifest=_manifest(
            stages=(
                ("pre-gate-stop", "bin/stop.py"),
                ("post-gate", "bin/post.py"),
            )
        ),
        files={
            "bin/stop.py": "print('stop ran')\n",
            "bin/post.py": "print('post ran')\n",
        },
    )
    assert main(["open", "--title", "Switch off openspec", "--scope", _SWITCHES]) == 0
    base = _commit_all(repo, "extension and task")
    _write_switches(repo, _OFF_CR_001)
    operational = _commit_all(repo, "switch off openspec")
    (repo / "code.py").write_text("code\n", encoding="utf-8")
    regular = _commit_all(repo, "switch off plus code")
    _ci(monkeypatch)
    capsys.readouterr()

    # post-gate on the operational candidate: the stage runs as today.
    assert _stage_run(phase="post-gate", commit=operational, base=base) == 0
    out = capsys.readouterr().out
    assert "openspec | post ran" in out

    # pre-gate on a candidate whose diff leaves the lane's shape: the
    # stage runs as today.
    assert _stage_run(commit=regular, base=base) == 0
    out = capsys.readouterr().out
    assert "openspec | stop ran" in out


def test_agreement_the_project_requires_is_not_owed_on_the_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The project may require agreement; an operational change owes none.

    The NOT EXAMINED line prints unconditionally — the lane requires no
    agreement whatever the project configures.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(repo, _OFF_CR_001)
    head = _commit_all(repo, "switch off openspec")
    # The gate reads the project file from the working tree, so the
    # agreement requirement stays uncommitted — a committed project.json
    # would leave the lane's shape.
    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["require_agreement"] = True
    project_path.write_text(json.dumps(project), encoding="utf-8")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "NOT EXAMINED: agreement (the operational lane requires none)" in output


def test_named_documents_are_still_checked_on_the_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A contract naming documents is still bound by them on the lane.

    Review, independence and agreement are what the lane requires none
    of; a named document the diff cannot touch is a different check and
    still fails.
    """

    repo = _project(tmp_path, monkeypatch)
    _write_extension_manifest(repo)
    assert main(["open", "--title", "Switch off openspec", "--scope", _SWITCHES]) == 0
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8")
        .replace("schema = 1", "schema = 2")
        .replace("acceptance = []", 'acceptance = []\ndocuments = ["openspec/specs/"]'),
        encoding="utf-8",
    )
    base = _commit_all(repo, "extension and task")
    _write_switches(repo, _OFF_CR_001)
    head = _commit_all(repo, "switch off openspec")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: named documents untouched: openspec/specs/" in output


def test_declared_rules_reviewers_and_implementers_on_the_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Declared review machinery is NOT EXAMINED; declared implementers still run.

    A contract declaring independence rules and reviewers gets a
    NOT EXAMINED line each; the implementers check is not review-bound,
    so it still runs — here against an in-range session whose actor is
    not a declared implementer.
    """

    repo = _project(tmp_path, monkeypatch)
    _write_extension_manifest(repo)
    assert main(["open", "--title", "Switch off openspec", "--scope", _SWITCHES]) == 0
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8")
        .replace("schema = 1", "schema = 3")
        .replace(
            "acceptance = []",
            "acceptance = []\n"
            'independence = ["distinct-actor"]\n'
            'reviewers = ["alice"]\n'
            'implementers = ["alice"]',
        ),
        encoding="utf-8",
    )
    base = _commit_all(repo, "extension and task")
    _write_switches(repo, _OFF_CR_001)
    head = _commit_all(repo, "switch off openspec")
    write_record(
        repo / ".agentmarshal" / "journal",
        "CR-001",
        create_session_record(
            "CR-001",
            "1.0",
            "implementer",
            "bob",
            "implementation",
            "done",
            1,
            2,
            3,
            commit=head,
        ),
    )
    head = _commit_all(repo, "a session under another actor")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert (
        "NOT EXAMINED: independence rule 'distinct-actor' "
        "(the operational lane requires no review)"
    ) in output
    assert "NOT EXAMINED: declared reviewers" in output
    assert (
        "FAIL: in-range implementer session actors outside the "
        "contract's declared implementers"
    ) in output


def test_the_count_line_stays_silent_on_the_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No review loop exists on the lane, so no count line prints.

    The regular and findings lanes report the changes_required count;
    the journal-only and operational lanes suppress it alike.
    """

    repo, base = _operational_repo(tmp_path, monkeypatch)
    _write_switches(repo, _OFF_CR_001)
    head = _commit_all(repo, "switch off openspec")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "changes_required verdicts" not in output


def test_the_switches_module_imports_in_either_order() -> None:
    """`import agentmarshal.switches` alone must not hit the import cycle.

    gate.py's former `from agentmarshal.switches import ...` asked a
    partially initialized module for its names: switches imports
    journal.contracts, whose package __init__ reaches gate through
    review.py. gate.py now binds the module itself and reads its
    attributes at call time, so either module imports first. Exercised
    in a subprocess under -I, the way the advisory reproduced it.
    """

    for module in ("agentmarshal.switches", "agentmarshal.journal.gate"):
        result = subprocess.run(
            [sys.executable, "-I", "-c", f"import {module}"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
