"""``status --base`` — records in the working tree the ref does not hold (CR-210).

Proposal 035's read side: `status <task> --base <ref>` prints, after the
detail view, the task's records present in the journal's working tree but
absent from `<ref>` — one line each with id and type — or one line saying
there are none. The ref resolves in the journal's own repository — under
a sidecar placement the sidecar's, never the host's — an unknown ref
refuses naming it, and without `--base` the command prints exactly what
it prints today.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_amendment_record,
    create_opened_record,
    create_session_record,
    write_record,
)
from test_placement import _commit, _host_and_sidecar

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]

_CONTRACT = """\
+++
schema = 1
id = "CR-001"
title = "Listing task"
scope = ["src/"]
acceptance = []
+++

# CR-001: Listing task
"""


def _commit_all(repo: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", *_WRITER, "commit", "--quiet", "-m", message],
        cwd=repo,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _record_id(path: Path) -> str:
    return path.name.removesuffix(".json").rsplit("-", 1)[0]


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """An embedded project holding task CR-001's contract and opened record.

    The opened record's id and time are fixed so the detail view can be
    pinned byte for byte.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    journal = repo / ".agentmarshal" / "journal"
    task_directory = journal / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(_CONTRACT, encoding="utf-8")
    opened = create_opened_record("CR-001", "1.0")
    opened["created_at"] = "2026-01-01T00:00:00Z"
    write_record(journal, "CR-001", opened, record_id="00000000000000000000000001")
    monkeypatch.chdir(repo)
    return repo, journal


def _session() -> dict[str, object]:
    return create_session_record(
        "CR-001", "1.0", "implementer", "impl", "implementation", "done", 1, 2, 3
    )


def test_records_the_ref_does_not_hold_are_listed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: records the ref does not hold are listed.

    The committed records stand at the ref; the ones written since do
    not — each prints its id and type after the detail view.
    """

    repo, journal = _project(tmp_path, monkeypatch)
    base = _commit_all(repo, "open")
    session = write_record(journal, "CR-001", _session())
    amendment = write_record(
        journal, "CR-001", create_amendment_record("CR-001", "1.0", "scope fix")
    )
    capsys.readouterr()

    assert main(["status", "CR-001", "--base", base]) == 0

    out = capsys.readouterr().out
    section = out.index(f"Records absent from {base}:")
    assert section > out.index("Records:")
    assert out[section:].splitlines() == [
        f"Records absent from {base}:",
        f"- {_record_id(session)} session",
        f"- {_record_id(amendment)} amendment",
    ]


def test_no_records_the_ref_lacks_prints_one_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: no records the ref lacks prints one line."""

    repo, _journal = _project(tmp_path, monkeypatch)
    _commit_all(repo, "open")
    capsys.readouterr()

    assert main(["status", "CR-001", "--base", "master"]) == 0

    out = capsys.readouterr().out
    assert out.endswith("Records absent from master: (none)\n")


def test_without_base_the_view_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: without --base the view is unchanged.

    The flagless output is pinned byte for byte: the records' fixed ids
    and times make the whole detail view literal.
    """

    repo, journal = _project(tmp_path, monkeypatch)
    session = _session()
    session["created_at"] = "2026-01-02T00:00:00Z"
    write_record(journal, "CR-001", session, record_id="00000000000000000000000002")
    _commit_all(repo, "open")
    capsys.readouterr()

    assert main(["status", "CR-001"]) == 0

    out = capsys.readouterr().out
    assert out == (
        "ID: CR-001\n"
        "Status: open\n"
        "Title: Listing task\n"
        "Scope:\n"
        "- src/\n"
        "Records:\n"
        "- 00000000000000000000000001 opened 2026-01-01T00:00:00Z\n"
        "- 00000000000000000000000002 session 2026-01-02T00:00:00Z\n"
        "No agreement with the contract is recorded\n"
    )


def test_an_unknown_ref_refuses_naming_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an unknown ref refuses naming it."""

    _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(["status", "CR-001", "--base", "no-such-ref"]) == 1

    captured = capsys.readouterr()
    assert "unknown base ref: no-such-ref" in captured.err
    assert captured.out == ""


def test_a_sidecar_compares_against_the_journal_repositorys_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a sidecar compares against the journal repository's ref.

    The ref below exists only in the sidecar — the journal's repository;
    resolving it there and not in the host's is what makes the comparison
    answer at all.
    """

    _host, sidecar, _base, _head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Private", "--scope", "app.txt"]) == 0
    journal = sidecar / ".agentmarshal" / "journal"
    base = _commit(sidecar, "open")
    record = write_record(journal, "CR-001", _session())
    capsys.readouterr()

    assert main(["status", "CR-001", "--base", base]) == 0

    out = capsys.readouterr().out
    assert f"Records absent from {base}:" in out
    assert f"- {_record_id(record)} session" in out


def test_a_value_the_listing_prints_is_escaped_on_display(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a value the listing prints is escaped on display.

    The ref is the listing's one caller-controlled value: a refused
    character in it prints as its escape, in the refusal as on the
    listing's own lines.
    """

    _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(["status", "CR-001", "--base", "bogus\nref"]) == 1

    err = capsys.readouterr().err
    assert "bogus\\nref" in err
    assert "bogus\nref" not in err


def test_base_without_a_task_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: --base without a task is refused.

    The listing is per task — with no task named there is nothing to
    hold the flag against, and the command says so.
    """

    _project(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(["status", "--base", "master"]) == 1

    assert "--base applies only to a named task" in capsys.readouterr().err
