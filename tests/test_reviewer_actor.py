"""Tests for the review commands' ``--actor`` flag (ADR-0018 D3, ADR-0022 s2).

``--actor`` names the declared reviewer actor the review record's
``reviewer`` object carries — the id the ``reviewers`` membership and
``distinct-actor`` checks a later task adds to the gate will compare.
``recorded_by`` — who wrote the record — stays the orthogonal stamp it
was, resolved from the environment by ``write_record`` as before.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import cast

import pytest

from agentmarshal import __version__
from agentmarshal.cli import main
from agentmarshal.journal.records import read_records
from test_review_launcher import (
    _finding_args,
    _finding_verdict,
    _record_finding,
    _review_args,
    _review_repo,
    _reviewer_stub,
    _verdict,
)


@pytest.fixture(autouse=True)
def _isolated_temp_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    system_temp = Path(tempfile.gettempdir())
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)
    return system_temp


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _submit_review_args() -> list[str]:
    return [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        "a" * 40,
        "--verdict",
        "approved",
        "--role",
        "reviewer",
        "--vendor",
        "human",
        "--model",
        "none",
        "--email",
        "reviewer@test.invalid",
    ]


def _records(repo: Path) -> list[dict[str, object]]:
    return read_records(_journal(repo), "CR-001")


def _review_record_files(repo: Path) -> list[Path]:
    return sorted(
        (_journal(repo) / "tasks" / "CR-001" / "records").glob("*-review.json")
    )


def _declare_actors(repo: Path, *actor_ids: str) -> None:
    """Write the project file's ``actors`` section declaring the given ids."""

    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["actors"] = {actor_id: {"git_identities": []} for actor_id in actor_ids}
    project_path.write_text(json.dumps(project), encoding="utf-8")


def test_submit_review_actor_records_the_reviewer_actor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: submit-review --actor records the reviewer actor."""

    repo, _commit = _review_repo(tmp_path, monkeypatch)

    assert main([*_submit_review_args(), "--actor", "claude"]) == 0

    record = _records(repo)[-1]
    assert cast(dict[str, object], record["reviewer"])["actor"] == "claude"
    assert record["schema"] == 7


def test_submit_review_actor_records_the_reviewer_actor_on_a_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: submit-review --actor records the reviewer actor.

    The finding binding shares the flag with the commit binding — the
    record's one-subject rule is unaffected.
    """

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    finding = _record_finding(repo, [("evidence.txt", b"conclusion\n")])
    arguments = _submit_review_args()
    commit_at = arguments.index("--commit")
    arguments[commit_at : commit_at + 2] = ["--reviewed-finding", finding]

    assert main([*arguments, "--actor", "claude"]) == 0

    record = _records(repo)[-1]
    assert cast(dict[str, object], record["reviewer"])["actor"] == "claude"
    assert record["reviewed_finding"] == finding
    assert record["schema"] == 7


def test_review_actor_records_the_reviewer_actor_on_a_commit_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: review --actor records the reviewer actor on a commit
    review."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert main([*_review_args(commit), "--actor", "claude"]) == 0

    record = _records(repo)[-1]
    assert cast(dict[str, object], record["reviewer"])["actor"] == "claude"
    assert record["schema"] == 7


def test_review_actor_records_the_reviewer_actor_on_a_finding_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: review --actor records the reviewer actor on a finding
    review."""

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    finding = _record_finding(repo, [("evidence.txt", b"conclusion\n")])
    stub = _reviewer_stub(tmp_path, _finding_verdict(finding, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert main([*_finding_args(finding), "--actor", "claude"]) == 0

    record = _records(repo)[-1]
    assert cast(dict[str, object], record["reviewer"])["actor"] == "claude"
    assert record["reviewed_finding"] == finding
    assert record["schema"] == 7


def test_the_reviewer_actor_is_not_confused_with_recorded_by(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the reviewer actor is not confused with recorded_by.

    The recorder resolves from the environment as before; the reviewer
    actor is the flag's own value. The record keeps both.
    """

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "the-recorder")

    assert main([*_submit_review_args(), "--actor", "the-reviewer"]) == 0

    record = _records(repo)[-1]
    assert record["recorded_by"] == "the-recorder"
    assert record["recorded_by_source"] == "override"
    assert cast(dict[str, object], record["reviewer"])["actor"] == "the-reviewer"


def test_a_review_written_without_actor_is_byte_for_byte_as_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a review written without --actor is byte-for-byte as
    before.

    The pin is the whole record apart from its id — the ULID in the
    file's name — and its ``created_at`` time: every field, the field
    set of ``reviewer``, and the schema stamp are the record the command
    wrote before the flag existed, and so are the lines it prints.
    """

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "operator")
    capsys.readouterr()

    assert main(_submit_review_args()) == 0

    files = _review_record_files(repo)
    assert len(files) == 1
    record = json.loads(files[0].read_text(encoding="utf-8"))
    expected = {
        "created_at": record["created_at"],
        "findings": [],
        "record_type": "review",
        "recorded_by": "operator",
        "recorded_by_source": "override",
        "reviewed_commit": "a" * 40,
        "reviewer": {
            "role": "reviewer",
            "vendor": "human",
            "model": "none",
            "email": "reviewer@test.invalid",
        },
        "schema": 3,
        "source": "live",
        "task": "CR-001",
        "tool_version": __version__,
        "verdict": "approved",
    }
    assert files[0].read_text(encoding="utf-8") == (
        json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    captured = capsys.readouterr()
    assert captured.out == f"{files[0]}\n"
    assert captured.err == ""


def test_a_launched_review_written_without_actor_is_byte_for_byte_as_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a review written without --actor is byte-for-byte as
    before.

    The launcher's record differs from ``submit-review``'s only by the
    ``reviewed_contract`` the launch path pins and the schema 5 stamp
    that carries — the pin below is literal about both, hashing the
    contract file's bytes the way the record does.
    """

    repo, commit = _review_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "operator")
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(_review_args(commit)) == 0

    files = _review_record_files(repo)
    assert len(files) == 1
    record = json.loads(files[0].read_text(encoding="utf-8"))
    contract = (_journal(repo) / "tasks" / "CR-001" / "contract.md").read_bytes()
    expected = {
        "created_at": record["created_at"],
        "findings": [],
        "record_type": "review",
        "recorded_by": "operator",
        "recorded_by_source": "override",
        "reviewed_commit": commit,
        "reviewed_contract": hashlib.sha256(contract).hexdigest(),
        "reviewer": {
            "role": "reviewer",
            "vendor": "test",
            "model": "test-model",
            "email": "reviewer@example.invalid",
        },
        "schema": 5,
        "source": "live",
        "task": "CR-001",
        "tool_version": __version__,
        "verdict": "approved",
        "artifacts": record["artifacts"],
    }
    assert files[0].read_text(encoding="utf-8") == (
        json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    captured = capsys.readouterr()
    assert captured.out == f"{files[0]}\n"
    record_id = files[0].name[: -len("-review.json")]
    assert captured.err == (
        "reviewer prose pinned: .agentmarshal/journal/tasks/CR-001/artifacts/"
        f"{record_id}-review.md\n"
    )


@pytest.mark.parametrize("actor", ["", "   ", "ok\nforged"])
def test_submit_review_refuses_a_refused_actor_value_before_writing(
    actor: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: submit-review refuses a refused actor value before
    writing."""

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main([*_submit_review_args(), "--actor", actor]) == 1

    assert "--actor" in capsys.readouterr().err
    assert _review_record_files(repo) == []


@pytest.mark.parametrize("actor", ["", "   ", "ok\nforged"])
def test_the_launcher_refuses_a_refused_actor_value_before_the_reviewer_runs(
    actor: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the launcher refuses a refused actor value before the
    reviewer runs.

    A launched reviewer costs a paid run, so the flag is refused before
    the command starts — the stub's marker file is what would prove it
    ran, and it never exists.
    """

    repo, commit = _review_repo(tmp_path, monkeypatch)
    ran = tmp_path / "reviewer-ran.txt"
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []), prompt_output=ran)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main([*_review_args(commit), "--actor", actor]) == 1

    assert "--actor" in capsys.readouterr().err
    assert not ran.exists()
    assert _review_record_files(repo) == []


@pytest.mark.parametrize("actor", ["", "   ", "ok\nforged"])
def test_the_dry_run_refuses_a_refused_actor_value_before_the_reviewer_runs(
    actor: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the dry run refuses a refused actor value before the
    reviewer runs."""

    _review_repo(tmp_path, monkeypatch)
    ran = tmp_path / "reviewer-ran.txt"
    stub = _reviewer_stub(
        tmp_path,
        _verdict("0" * 40, "approved", []),
        prompt_output=ran,
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(["review", "--dry-run", "--actor", actor]) == 1

    assert "--actor" in capsys.readouterr().err
    assert not ran.exists()


def test_an_undeclared_reviewer_actor_is_accepted_and_noted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an undeclared reviewer actor is accepted and noted.

    The project declares no actors table at all: the record stands —
    declared, never authenticated — and the command says the actor is
    not a declared actor.
    """

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main([*_submit_review_args(), "--actor", "claude"]) == 0

    record = _records(repo)[-1]
    assert cast(dict[str, object], record["reviewer"])["actor"] == "claude"
    assert "claude is not a declared actor" in capsys.readouterr().err


def test_a_declared_reviewer_actor_is_recorded_with_no_note(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a declared reviewer actor is recorded with no note."""

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    _declare_actors(repo, "claude")
    capsys.readouterr()

    assert main([*_submit_review_args(), "--actor", "claude"]) == 0

    record = _records(repo)[-1]
    assert cast(dict[str, object], record["reviewer"])["actor"] == "claude"
    assert "is not a declared actor" not in capsys.readouterr().err


def test_a_dry_run_shows_the_actor_it_would_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a dry run shows the actor it would record."""

    repo, _commit = _review_repo(tmp_path, monkeypatch)
    _declare_actors(repo, "claude")
    stub = _reviewer_stub(tmp_path, _verdict("0" * 40, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(["review", "--dry-run", "--actor", "claude"]) == 0

    captured = capsys.readouterr()
    assert "nothing was recorded" in captured.out
    assert "claude" in captured.out
    assert "is not a declared actor" not in captured.err


def test_a_dry_run_notes_an_undeclared_actor_as_a_recorded_run_does(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a dry run notes an undeclared actor as a recorded run
    does."""

    _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict("0" * 40, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(["review", "--dry-run", "--actor", "claude"]) == 0

    captured = capsys.readouterr()
    assert "claude" in captured.out
    assert "claude is not a declared actor" in captured.err
