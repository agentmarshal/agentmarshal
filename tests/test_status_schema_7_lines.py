"""Pin the schema-7 record lines in the per-task ``status`` view (CR-184).

`check`, `agreement`, `acknowledgement` and `ext` records render on lines
of their own — through the renderer registry like every record type that
has one — each naming its recorder, and a recorder that is not a declared
actor is shown as such (ADR-0022 section 3). An acknowledgement whose
recorder is a declared writer of the acknowledged commit is marked
self-acknowledged, derived on display the way self-acceptance is
(ADR-0021 decision 5). The agreement line after the records says no
agreement is recorded or that the latest agreement is for an earlier
contract text — against the contract's current hash, not its pin
(ADR-0018 decision 2).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.contracts import ContractHeader, contract_sha256
from agentmarshal.journal.records import (
    create_acknowledgement_record,
    create_agreement_record,
    create_check_record,
    create_ext_record,
    create_opened_record,
    write_record,
)
from agentmarshal.journal.status import TaskStatus
from agentmarshal.journal.status_view import print_task_detail

_COMMIT = "a" * 40
_CONTRACT_HASH = "b" * 64
_OTHER_HASH = "c" * 64

_CONTRACT = """\
+++
schema = 1
id = "CR-001"
title = "Task"
scope = []
acceptance = []
+++

# CR-001: Task
"""


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    A schema-7 record requires a resolvable recorder, and the ambient
    `AGENTMARSHAL_ACTOR` must not decide what a test resolves — every test
    that needs a recorder names the actor itself.
    """

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    actors: dict[str, Any] | None = None,
) -> Path:
    """A git root with project.json and the task's contract — the floor."""

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    agentmarshal = repo / ".agentmarshal"
    agentmarshal.mkdir()
    project: dict[str, Any] = {"schema": 1}
    if actors:
        project["actors"] = actors
    (agentmarshal / "project.json").write_text(
        json.dumps(project) + "\n", encoding="utf-8"
    )
    task_directory = agentmarshal / "journal" / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(_CONTRACT, encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _commit_file(repo: Path, name: str, content: str) -> str:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", name], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--quiet",
            "-m",
            name,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write(
    repo: Path, record: dict[str, object], record_id: str, created_at: str
) -> None:
    record["created_at"] = created_at
    write_record(_journal(repo), "CR-001", record, record_id=record_id)


def _current_hash(repo: Path) -> str:
    contract = _journal(repo) / "tasks" / "CR-001" / "contract.md"
    return contract_sha256(contract.read_bytes(), str(contract))


# -- the four record types render on lines of their own ----------------------


def test_a_check_record_renders_name_result_commit_failed_step_and_recorder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status shows a check record on a line of its own."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_check_record(
            "CR-001", "1.0", _COMMIT, "lint", "failed", failed_step="ruff"
        ),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )
    _write(
        repo,
        create_check_record("CR-001", "1.0", _COMMIT, "pytest", "passed"),
        "00000000000000000000000003",
        "2026-01-03T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- 00000000000000000000000002 check 2026-01-02T00:00:00Z "
        f"name=lint result=failed commit={_COMMIT[:7]} "
        "failed_step=ruff recorded_by=an-operator (not a declared actor)\n"
    ) in out
    assert (
        "- 00000000000000000000000003 check 2026-01-03T00:00:00Z "
        f"name=pytest result=passed commit={_COMMIT[:7]} "
        "recorded_by=an-operator (not a declared actor)\n"
    ) in out


def test_an_agreement_record_renders_the_short_hash_and_who_agreed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status shows an agreement record on a line of its own."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_agreement_record("CR-001", "1.0", _current_hash(repo)),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    record_line = (
        f"- 00000000000000000000000002 agreement 2026-01-02T00:00:00Z "
        f"contract={_current_hash(repo)[:7]} "
        "recorded_by=ops-lead (not a declared actor)"
    )
    assert record_line in lines
    # The agreement is for the current text: no summary line follows the
    # records.
    assert lines[-1] == record_line


def test_an_acknowledgement_renders_commit_file_signature_recorder_and_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status shows an acknowledgement record on a line of its own."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_acknowledgement_record(
            "CR-001",
            "1.0",
            _COMMIT,
            "src/app.py",
            "Reviewed: an example key in documentation",
            signature="openai-key",
        ),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )
    _write(
        repo,
        create_acknowledgement_record(
            "CR-001",
            "1.0",
            _COMMIT,
            "README.md",
            "Reviewed: a placeholder",
            signature=None,
            marker=3,
        ),
        "00000000000000000000000003",
        "2026-01-03T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- 00000000000000000000000002 acknowledgement 2026-01-02T00:00:00Z "
        f"commit={_COMMIT[:7]} file=src/app.py signature=openai-key "
        "recorded_by=an-operator (not a declared actor) "
        "reason=Reviewed: an example key in documentation "
        "self-acknowledgement not checked\n"
    ) in out
    assert (
        "- 00000000000000000000000003 acknowledgement 2026-01-03T00:00:00Z "
        f"commit={_COMMIT[:7]} file=README.md marker=3 "
        "recorded_by=an-operator (not a declared actor) "
        "reason=Reviewed: a placeholder "
        "self-acknowledgement not checked\n"
    ) in out


def test_an_ext_record_renders_kind_commit_payload_hash_and_recorder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: status shows an ext record on a line of its own."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    record = create_ext_record(
        "CR-001", "1.0", "vendor/audit@1", _COMMIT, {"verdict": "clean"}
    )
    _write(repo, record, "00000000000000000000000002", "2026-01-02T00:00:00Z")

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert (
        "- 00000000000000000000000002 ext 2026-01-02T00:00:00Z "
        f"kind=vendor/audit@1 commit={_COMMIT[:7]} "
        f"payload_sha256={str(record['payload_sha256'])[:7]} "
        "recorded_by=an-operator (not a declared actor)\n"
    ) in out


# -- the recorder ------------------------------------------------------------


def test_a_recorder_who_is_not_a_declared_actor_is_shown_as_such(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a recorder that is not a declared actor is shown as such."""

    repo = _repo(tmp_path, monkeypatch, actors={"lead": {"git_identities": []}})
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "a-stranger")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_check_record("CR-001", "1.0", _COMMIT, "lint", "passed"),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )
    _write(
        repo,
        create_agreement_record("CR-001", "1.0", _current_hash(repo)),
        "00000000000000000000000003",
        "2026-01-03T00:00:00Z",
    )
    _write(
        repo,
        create_acknowledgement_record(
            "CR-001", "1.0", _COMMIT, "f.py", "ok", signature="openai-key"
        ),
        "00000000000000000000000004",
        "2026-01-04T00:00:00Z",
    )
    _write(
        repo,
        create_ext_record("CR-001", "1.0", "vendor/audit@1", _COMMIT, {}),
        "00000000000000000000000005",
        "2026-01-05T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert out.count("recorded_by=a-stranger (not a declared actor)") == 4


def test_a_declared_recorder_is_shown_without_the_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a declared recorder is named without the note."""

    repo = _repo(
        tmp_path,
        monkeypatch,
        actors={"lead": {"git_identities": ["lead@example.invalid"]}},
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "lead")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_check_record("CR-001", "1.0", _COMMIT, "lint", "passed"),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert "recorded_by=lead\n" in out
    assert "not a declared actor" not in out


# -- self-acknowledgement ----------------------------------------------------


def test_an_acknowledgement_by_the_commits_writer_is_marked_self_acknowledged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acknowledgement by a declared writer of the commit is
    marked self-acknowledged — the ADR-0007 derivation applied on display,
    never stored."""

    repo = _repo(tmp_path, monkeypatch)
    commit = _commit_file(repo, "src/app.py", "key = 'x'\n")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "test@example.invalid")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_acknowledgement_record(
            "CR-001", "1.0", commit, "src/app.py", "ok", signature="openai-key"
        ),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert " self-acknowledged\n" in out
    record = json.loads(
        next(
            (_journal(repo) / "tasks" / "CR-001" / "records").glob(
                "00000000000000000000000002*.json"
            )
        ).read_text(encoding="utf-8")
    )
    assert "self" not in record


def test_an_acknowledgement_by_another_actor_is_not_marked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acknowledgement by another actor is not marked."""

    repo = _repo(tmp_path, monkeypatch)
    commit = _commit_file(repo, "src/app.py", "key = 'x'\n")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "someone-else")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_acknowledgement_record(
            "CR-001", "1.0", commit, "src/app.py", "ok", signature="openai-key"
        ),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    line = next(line for line in out.splitlines() if " acknowledgement " in line)
    assert "self-acknowledg" not in line


def test_an_acknowledgement_git_cannot_read_says_the_mark_was_not_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: where git cannot read the commit the line says the mark
    was not checked."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_acknowledgement_record(
            "CR-001",
            "1.0",
            _COMMIT,  # a hash the repository does not hold
            "src/app.py",
            "ok",
            signature="openai-key",
        ),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert " self-acknowledgement not checked\n" in out


def test_an_acknowledgement_through_the_actors_table_marks_self_acknowledged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acknowledgement whose recorded_by resolves through the
    actors table to a writer of the commit is marked self-acknowledged."""

    repo = _repo(
        tmp_path,
        monkeypatch,
        actors={"lead": {"git_identities": ["test@example.invalid"]}},
    )
    commit = _commit_file(repo, "src/app.py", "key = 'x'\n")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "lead")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_acknowledgement_record(
            "CR-001", "1.0", commit, "src/app.py", "ok", signature="openai-key"
        ),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert " self-acknowledged\n" in out


# -- the agreement line ------------------------------------------------------


def test_a_task_with_no_agreement_says_no_agreement_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task with no agreement record prints one line saying no
    agreement is recorded — after the record lines, without failing the
    command or changing the task's state."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1] == "No agreement with the contract is recorded"
    assert lines[-2].startswith("- ") and " opened " in lines[-2]


def test_an_agreement_for_an_earlier_contract_text_is_said(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task whose latest agreement's hash differs from the
    contract's current hash says the agreement is for an earlier text,
    naming both short hashes."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_agreement_record("CR-001", "1.0", _CONTRACT_HASH),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[-1] == (
        f"Recorded agreement {_CONTRACT_HASH[:7]} is for an earlier "
        f"contract text (now {_current_hash(repo)[:7]})"
    )


def test_the_agreement_line_compares_against_the_current_hash_not_the_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the agreement-for-an-earlier-text line compares with the
    contract's current hash — a drifted contract whose pin still equals
    the agreed hash still prints the earlier-text line beside the drift
    line."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    pinned = _current_hash(repo)
    opened = create_opened_record("CR-001", "1.0", contract=pinned)
    _write(repo, opened, "00000000000000000000000001", "2026-01-01T00:00:00Z")
    _write(
        repo,
        create_agreement_record("CR-001", "1.0", pinned),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )
    # The contract drifts: the file changes and no amendment pins it.
    contract = _journal(repo) / "tasks" / "CR-001" / "contract.md"
    contract.write_text(_CONTRACT + "\nMore.\n", encoding="utf-8")
    drifted = _current_hash(repo)
    assert drifted != pinned

    assert main(["status", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[-2] == (
        f"Recorded agreement {pinned[:7]} is for an earlier contract "
        f"text (now {drifted[:7]})"
    )
    assert lines[-1] == (
        f"Contract drifted from its pin {pinned[:7]} (now {drifted[:7]}); "
        "record the edit with amend"
    )


def test_an_agreement_at_the_current_hash_prints_no_agreement_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task whose latest agreement names the contract's
    current hash prints no agreement line after the records."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    _write(
        repo,
        create_opened_record("CR-001", "1.0"),
        "00000000000000000000000001",
        "2026-01-01T00:00:00Z",
    )
    _write(
        repo,
        create_agreement_record("CR-001", "1.0", _current_hash(repo)),
        "00000000000000000000000002",
        "2026-01-02T00:00:00Z",
    )

    assert main(["status", "CR-001"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert "agreement is recorded" not in capsys.readouterr().out
    assert lines[-1].startswith("- ")


# -- escaping ----------------------------------------------------------------


def test_every_value_from_the_schema_7_lines_prints_escaped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every value taken from a check, agreement,
    acknowledgement or ext record prints escaped — a hostile value stays
    on the one line it belongs to."""

    task = TaskStatus(
        task_id="CR-001",
        contract=ContractHeader(
            schema=1, id="CR-001", title="Task", scope=(), acceptance=()
        ),
        records=(
            {
                "id": "r-check",
                "record_type": "check",
                "created_at": "t0",
                "commit": "a" * 40,
                "name": "li\u202ent",
                "result": "failed\nforged",
                "failed_step": "st\nep",
                "recorded_by": "op\nerator",
                "recorded_by_source": "override",
            },
            {
                "id": "r-agreement",
                "record_type": "agreement",
                "created_at": "t1",
                "contract": "b\u202e" + "b" * 62,
                "recorded_by": "lead\u202e",
                "recorded_by_source": "override",
            },
            {
                "id": "r-ack",
                "record_type": "acknowledgement",
                "created_at": "t2",
                "commit": "a" * 40,
                "file": "src/\u202epp.py",
                "signature": "open\nai-key",
                "reason": "fine\ngate: passed",
                "recorded_by": "an-operator",
                "recorded_by_source": "override",
            },
            {
                "id": "r-ack-marker",
                "record_type": "acknowledgement",
                "created_at": "t3",
                "commit": "a" * 40,
                "file": "f.py",
                "marker": 4,
                "reason": "ok",
                "recorded_by": "an-operator",
                "recorded_by_source": "override",
            },
            {
                "id": "r-ext",
                "record_type": "ext",
                "created_at": "t4",
                "kind": "vendor\n/audit@1",
                "commit": "a" * 40,
                "payload": {},
                "payload_sha256": "d\u202e" + "d" * 62,
                "recorded_by": "ex\nt",
                "recorded_by_source": "override",
            },
        ),
        state="open",
    )

    print_task_detail(tmp_path, task, tmp_path)

    assert capsys.readouterr().out == (
        "ID: CR-001\n"
        "Status: open\n"
        "Title: Task\n"
        "Scope:\n"
        "- (none)\n"
        "Records:\n"
        "- r-check check t0 name=li\\u202ent result=failed\\nforged "
        "commit=aaaaaaa failed_step=st\\nep "
        "recorded_by=op\\nerator (not a declared actor)\n"
        "- r-agreement agreement t1 contract=b\\u202e"
        "bbbbb "
        "recorded_by=lead\\u202e (not a declared actor)\n"
        "- r-ack acknowledgement t2 commit=aaaaaaa file=src/\\u202epp.py "
        "signature=open\\nai-key "
        "recorded_by=an-operator (not a declared actor) "
        "reason=fine\\ngate: passed self-acknowledgement not checked\n"
        "- r-ack-marker acknowledgement t3 commit=aaaaaaa file=f.py "
        "marker=4 recorded_by=an-operator (not a declared actor) "
        "reason=ok self-acknowledgement not checked\n"
        "- r-ext ext t4 kind=vendor\\n/audit@1 commit=aaaaaaa "
        "payload_sha256=d\\u202e"
        "ddddd "
        "recorded_by=ex\\nt (not a declared actor)\n"
    )
