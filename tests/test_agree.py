"""`agentmarshal agree` — one actor agreeing with a task's contract.

ADR-0018 decision 2 / ADR-0022 section 3: a declared actor states agreement
with the contract at a stated hash — any declared actor may, there are no
roles, and an agreement does not gate anything. The command reads the
task's `contract.md` as it stands, hashes it with the one
`contract_sha256` every pin uses, and writes one `agreement` record.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture(autouse=True)
def _isolated_actor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    actors: dict[str, Any] | None = None,
) -> Path:
    """A git root with project.json — the embedded-placement floor."""

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    agentmarshal = repo / ".agentmarshal"
    agentmarshal.mkdir()
    project: dict[str, Any] = {"task": {"name": "agentmarshal"}}
    if actors:
        project["actors"] = actors
    (agentmarshal / "project.json").write_text(
        json.dumps(project) + "\n", encoding="utf-8"
    )
    monkeypatch.chdir(repo)
    return repo


def _open() -> None:
    from agentmarshal.cli import main

    assert main(["open", "--title", "Task"]) == 0


def _agree(*extra: str, task: str = "CR-001") -> int:
    from agentmarshal.cli import main

    return main(["agree", "--task", task, *extra])


def _records(repo: Path, task: str = "CR-001") -> list[dict[str, Any]]:
    records = sorted((_journal(repo) / "tasks" / task / "records").glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in records]


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _current_hash(repo: Path, task: str = "CR-001") -> str:
    from agentmarshal.journal.contracts import contract_sha256

    contract = _journal(repo) / "tasks" / task / "contract.md"
    return contract_sha256(contract.read_bytes(), str(contract))


# -- an agreement is written at the contract's current hash ------------------


def test_agreement_is_written_at_the_contracts_current_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an agreement is written at the contract's current hash.

    `agree` on an open task writes one `agreement` record at schema 7 whose
    `contract` is the `contract_sha256` of `contract.md` and whose
    `recorded_by` names the recorder; stdout prints the path, the hash and
    the recorder.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    current = _current_hash(repo)
    assert _agree() == 0
    records = _records(repo)
    agreements = [r for r in records if r["record_type"] == "agreement"]
    assert len(agreements) == 1
    agreement = agreements[0]
    assert agreement["schema"] == 7
    assert agreement["contract"] == current
    assert agreement["recorded_by"] == "ops-lead"
    assert agreement["recorded_by_source"] == "override"
    out = capsys.readouterr().out
    assert current in out
    assert "ops-lead" in out
    # The agreement record reads back through the schema-7 reader.
    from agentmarshal.journal.records import read_records

    loaded = read_records(_journal(repo), "CR-001")
    assert loaded[-1]["record_type"] == "agreement"
    assert loaded[-1]["contract"] == current


def test_an_unknown_task_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unknown task is refused writing nothing."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    before = _snapshot(_journal(repo))
    assert _agree(task="CR-099") == 1
    assert "unknown task" in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


@pytest.mark.parametrize("terminal", ["completed", "abandoned"])
def test_a_terminal_task_is_refused_writing_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    terminal: str,
) -> None:
    """Scenario: a completed or abandoned task is refused writing nothing.

    Terminal means closed — agreement after the work ended attests to
    nothing the gate can use.
    """

    from agentmarshal.journal.records import (
        create_abandoned_record,
        create_completed_record,
        write_record,
    )

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    if terminal == "completed":
        record = create_completed_record("CR-001", "test", "e" * 40)
    else:
        record = create_abandoned_record("CR-001", "test", "gone away")
    write_record(_journal(repo), "CR-001", record)
    before = _snapshot(_journal(repo))
    assert _agree() == 1
    assert "not open" in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


def test_a_completed_task_with_a_later_check_is_still_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a completed task that accrued a check is still refused.

    `check` is admitted after terminal records but reopens nothing — the
    projection's terminal state stands and agreement is still refused.
    """

    from agentmarshal.journal.records import (
        create_check_record,
        create_completed_record,
        write_record,
    )

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    journal = _journal(repo)
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", "e" * 40))
    write_record(
        journal,
        "CR-001",
        create_check_record("CR-001", "test", "f" * 40, "tests", "passed"),
    )
    before = _snapshot(journal)
    assert _agree() == 1
    assert "not open" in capsys.readouterr().err
    assert _snapshot(journal) == before


def test_agreement_is_recorded_more_than_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: agreement is recorded more than once on the same task.

    Each `agree` is one attestation at the hash then current — a second
    agreement appends a second record rather than being deduplicated.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    assert _agree() == 0
    assert _agree() == 0
    records_dir = _journal(repo) / "tasks" / "CR-001" / "records"
    agreements = sorted(records_dir.glob("*-agreement.json"))
    assert len(agreements) == 2
    for path in agreements:
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["record_type"] == "agreement"
        assert record["contract"] == _current_hash(repo)


def test_a_contract_read_with_crlf_endings_hashes_as_its_lf_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a contract read either way hashes the same.

    `contract_sha256` normalizes line endings before hashing, so the hash
    `agree` writes for a contract saved CRLF is the one the LF pin carries
    — the command agrees with the text, not the bytes' endings.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    contract = _journal(repo) / "tasks" / "CR-001" / "contract.md"
    lf_hash = _current_hash(repo)
    contract.write_bytes(contract.read_bytes().replace(b"\n", b"\r\n"))
    assert _agree() == 0
    agreements = [r for r in _records(repo) if r["record_type"] == "agreement"]
    assert agreements[0]["contract"] == lf_hash


# -- a drifted contract is refused until amend records it --------------------


def test_a_drifted_contract_is_refused_naming_the_pin_and_amend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a drifted contract is refused naming the pin and amend.

    When the task's pin and the current hash differ, `agree` refuses,
    naming both short hashes and `amend` — and writes nothing, even when
    `--contract` equals the pin.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    pinned = _current_hash(repo)
    contract = _journal(repo) / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8") + "\n- one more thing\n",
        encoding="utf-8",
    )
    current = _current_hash(repo)
    assert current != pinned
    before = _snapshot(_journal(repo))
    assert _agree() == 1
    err = capsys.readouterr().err
    assert pinned[:7] in err
    assert current[:7] in err
    assert "amend" in err
    assert _snapshot(_journal(repo)) == before
    # --contract equal to the pin does not rescue a drifted contract.
    assert _agree("--contract", pinned) == 1
    assert _snapshot(_journal(repo)) == before


def test_a_task_without_a_pin_agrees_at_the_current_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a task whose records carry no pin agrees at the current text.

    Tasks opened before contract hashes existed carry no `contract` field
    on any record — nothing was ever pinned, so nothing can have drifted
    and the agreement pins the current text.
    """

    from agentmarshal.journal.records import create_opened_record, write_record

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    task_dir = _journal(repo) / "tasks" / "CR-001"
    records_dir = task_dir / "records"
    records_dir.mkdir(parents=True)
    (task_dir / "contract.md").write_text(
        "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    opened = create_opened_record("CR-001", "test")  # schema 3: no contract pin
    write_record(_journal(repo), "CR-001", opened)
    assert _agree() == 0
    agreements = [r for r in _records(repo) if r["record_type"] == "agreement"]
    assert agreements[0]["contract"] == _current_hash(repo)


def test_the_latest_pin_is_the_one_compared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the latest hash-carrying pin is the one compared.

    After `amend` re-pins, agreement lands at the amendment's hash; when
    the contract drifts again it is the amendment's pin the refusal names.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    contract = _journal(repo) / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8") + "\n- amended goal\n",
        encoding="utf-8",
    )
    from agentmarshal.cli import main

    assert main(["amend", "--task", "CR-001", "--reason", "a change"]) == 0
    repinned = _current_hash(repo)
    assert _agree() == 0
    agreements = [r for r in _records(repo) if r["record_type"] == "agreement"]
    assert agreements[0]["contract"] == repinned
    contract.write_text(
        contract.read_text(encoding="utf-8") + "\n- drifted again\n",
        encoding="utf-8",
    )
    assert _agree() == 1
    assert repinned[:7] in capsys.readouterr().err


# -- --contract binds agreement to the hash the actor read ---------------------


def test_contract_argument_equal_to_the_current_hash_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: --contract equal to the contract's current hash writes.

    The flag pins the agreement to the text the actor actually read; when
    it equals the current hash the record lands at that hash.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    current = _current_hash(repo)
    assert _agree("--contract", current) == 0
    agreements = [r for r in _records(repo) if r["record_type"] == "agreement"]
    assert agreements[0]["contract"] == current


def test_contract_argument_differing_is_refused_naming_both_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: --contract differing is refused naming both hashes.

    A hash that parses but is not the current one means the actor read
    another text — the refusal names what was given and what is current,
    and writes nothing.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    current = _current_hash(repo)
    other = "0" * 63 + "1"
    assert other != current
    before = _snapshot(_journal(repo))
    assert _agree("--contract", other) == 1
    err = capsys.readouterr().err
    assert other in err
    assert current in err
    assert _snapshot(_journal(repo)) == before


@pytest.mark.parametrize(
    "bad",
    [
        "g" * 64,  # not hex
        "A" * 64,  # hex but uppercase
        "a" * 63,  # hex but short
        "a" * 65,  # hex but long
        "",  # empty
        "0x" + "a" * 64,  # prefixed
    ],
)
def test_contract_argument_in_the_wrong_shape_is_refused_naming_the_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    bad: str,
) -> None:
    """Scenario: --contract not exactly 64 lowercase hex is refused.

    The record family's contract field has one shape; a value that is not
    it is refused with `--contract` named, before the journal is touched.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _open()
    before = _snapshot(_journal(repo))
    assert _agree("--contract", bad) == 1
    assert "--contract" in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before


# -- the recorder is named, or nothing is written -----------------------------


def test_no_resolvable_recorder_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no resolvable recorder identity is refused writing nothing.

    No override, no project-actor match and no git identity leaves the
    record its rule requires nameless — `agree` refuses cleanly before
    anything is created.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    _open()  # opened records do not require a recorder
    before = _snapshot(_journal(repo))
    assert _agree() == 1
    err = capsys.readouterr().err
    assert "recorder" in err and "AGENTMARSHAL_ACTOR" in err
    assert _snapshot(_journal(repo)) == before


def test_a_recorder_who_is_not_a_declared_actor_is_accepted_and_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a recorder who is not a declared actor is accepted and named.

    Recorder is provenance, not permission — the record is written and
    the note says so plainly on stderr.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "a-stranger")
    _open()
    assert _agree() == 0
    agreements = [r for r in _records(repo) if r["record_type"] == "agreement"]
    assert agreements[0]["recorded_by"] == "a-stranger"
    assert "not a declared actor" in capsys.readouterr().err


def test_a_declared_actor_records_with_no_undeclared_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a declared actor records with no undeclared note.

    Whether the actor id resolves through the table or merely *names* a
    declared actor through the override, there is nothing to note.
    """

    repo = _repo(
        tmp_path,
        monkeypatch,
        actors={"lead": {"git_identities": ["lead@example.invalid"]}},
    )
    subprocess.run(
        ["git", "config", "user.email", "lead@example.invalid"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    _open()
    assert _agree() == 0
    out = capsys.readouterr()
    assert "lead" in out.out
    assert "declared actor" not in out.err
    # An override that names a declared actor is also quiet.
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "lead")
    assert _agree() == 0
    assert "declared actor" not in capsys.readouterr().err


def test_the_recorder_is_escaped_where_it_could_forge_a_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the recorder is escaped where it could forge a line.

    A recorder containing newline or line-separator bytes must not reorder
    or fabricate transcript lines — the escaped form is what prints, in
    the record line and in the undeclared-actor note alike.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "op\nera\u202etor")
    _open()
    assert _agree() == 0
    captured = capsys.readouterr()
    assert "op\nera\u202etor" not in captured.out + captured.err
    assert "op\\nera\\u202etor" in captured.out
    assert "op\\nera\\u202etor" in captured.err
    # The record itself keeps the true identity bytes.
    agreements = [r for r in _records(repo) if r["record_type"] == "agreement"]
    assert agreements[0]["recorded_by"] == "op\nera\u202etor"


def test_agree_lists_its_arguments_in_help(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command is registered from its own module: --task and --contract."""

    from agentmarshal.cli import main

    _repo(tmp_path, monkeypatch)
    with pytest.raises(SystemExit) as exited:
        main(["agree", "--help"])
    assert exited.value.code == 0
    out = capsys.readouterr().out
    assert "--task" in out
    assert "--contract" in out
