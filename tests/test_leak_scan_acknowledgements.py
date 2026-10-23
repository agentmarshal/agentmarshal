"""`agentmarshal leak-scan` honours the journal's acknowledgements.

ADR-0021 decisions 2 and 3: a record bound to the candidate's commit,
the file exactly as the scan prints it and the hit's identification
marks the hit — acknowledged, by whom and why — and an acknowledged
hit no longer makes the command exit 1, while a hit nobody
acknowledged still does. Every hit stays printed.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_acknowledgement_record,
    write_record,
)

_GITHUB_TOKEN = f"ghp_{'A1' * 18}"
_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
_MARKER = "internal.example.invalid"
_WRITER = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]


@pytest.fixture(autouse=True)
def _isolated_actor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    markers: tuple[str, ...] = (),
) -> Path:
    """A git root with the project initialized and one base commit."""

    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    if markers:
        project_file = repo / ".agentmarshal" / "project.json"
        data = json.loads(project_file.read_text(encoding="utf-8"))
        data["leak_scan"] = {"private_markers": list(markers)}
        project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _commit_all(repo, "base")
    return repo


def _add_file(repo: Path, path: str, content: str) -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _commit_all(repo, f"add {path}")


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD")


def _open() -> None:
    assert main(["open", "--title", "Task"]) == 0


def _acknowledge(
    base: str,
    head: str,
    *,
    task: str = "CR-001",
    file: str = "secret.py",
    signature: str = "github-token",
    marker: int | None = None,
    reason: str = "reviewed, not a leak",
) -> int:
    arguments = [
        "acknowledge",
        "--task",
        task,
        "--base",
        base,
        "--commit",
        head,
        "--file",
        file,
        "--reason",
        reason,
    ]
    if marker is not None:
        arguments += ["--marker", str(marker)]
    else:
        arguments += ["--signature", signature]
    return main(arguments)


def _write_acknowledgement(
    repo: Path,
    task: str,
    commit: str,
    file: str,
    reason: str,
    *,
    signature: str | None = "github-token",
    marker: int | None = None,
) -> None:
    record = create_acknowledgement_record(
        task,
        "test",
        commit,
        file,
        reason,
        signature if marker is None else None,
        marker=marker,
    )
    write_record(_journal(repo), task, record)


# -- reading the journal's records -------------------------------------------


def test_the_records_are_read_from_every_task_of_the_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the records are read from every task of the journal.

    Two hits, one acknowledged on CR-001 and the other on CR-002: the
    read is not scoped to any one task, so both hits are marked and the
    run exits 0.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    head = _add_file(repo, "other.py", f"key = '{_AWS_KEY}'\n")
    _open()  # CR-001
    _open()  # CR-002
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert (
        _acknowledge(
            base, head, task="CR-001", file="secret.py", signature="github-token"
        )
        == 0
    )
    assert (
        _acknowledge(
            base,
            head,
            task="CR-002",
            file="other.py",
            signature="aws-access-key-id",
            reason="second hit reviewed",
        )
        == 0
    )
    capsys.readouterr()

    code = main(["leak-scan", "--base", base, "--commit", head])

    output = capsys.readouterr().out
    assert code == 0
    assert (
        "other.py: aws-access-key-id "
        "(acknowledged by an-operator: second hit reviewed)" in output
    )
    assert (
        "secret.py: github-token "
        "(acknowledged by an-operator: reviewed, not a leak)" in output
    )


def test_task_reads_the_one_tasks_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: --task reads the one task's records.

    The acknowledgement sits on CR-002; `--task CR-001` does not read
    it and the hit stays unacknowledged, while `--task CR-002` reads it
    and the hit is marked.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()  # CR-001
    _open()  # CR-002
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head, task="CR-002") == 0
    capsys.readouterr()

    assert (
        main(["leak-scan", "--base", base, "--commit", head, "--task", "CR-001"]) == 1
    )
    output = capsys.readouterr().out
    assert "secret.py: github-token" in output
    assert "acknowledged" not in output

    assert (
        main(["leak-scan", "--base", base, "--commit", head, "--task", "CR-002"]) == 0
    )
    assert "acknowledged by an-operator" in capsys.readouterr().out


def test_a_task_that_cannot_be_read_acknowledges_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task that cannot be read acknowledges nothing.

    `--task` naming a task the journal does not carry — or one whose
    records fail reading — leaves no hit acknowledged and says why on
    stderr.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head) == 0
    capsys.readouterr()

    assert (
        main(["leak-scan", "--base", base, "--commit", head, "--task", "CR-099"]) == 1
    )
    captured = capsys.readouterr()
    assert "cannot read acknowledgements" in captured.err
    assert "CR-099" in captured.err
    assert "acknowledged" not in captured.out

    # A task that exists but cannot be read fares the same way: one
    # undecodable record file and the task's records fail the read.
    record_path = (
        _journal(repo) / "tasks" / "CR-001" / "records" / ("0" * 26 + "-opened.json")
    )
    record_path.write_text("{ not json", encoding="utf-8")
    assert (
        main(["leak-scan", "--base", base, "--commit", head, "--task", "CR-001"]) == 1
    )
    captured = capsys.readouterr()
    assert "cannot read acknowledgements" in captured.err
    assert "acknowledged" not in captured.out


def test_a_journal_that_cannot_be_read_acknowledges_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a journal that cannot be read acknowledges nothing.

    A real acknowledgement bound to the candidate sits on CR-001, but
    one task's records fail validation: the whole read counts as
    nothing and the command says why on stderr — the hit that a valid
    record names is unacknowledged.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()  # CR-001
    _open()  # CR-002
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head, task="CR-001") == 0
    # A record file that does not decode makes CR-002's records
    # unreadable — and with the whole-task read failing, nothing counts.
    records_dir = _journal(repo) / "tasks" / "CR-002" / "records"
    (records_dir / "0000000000000000000000000A-finding.json").write_text(
        "{ not json", encoding="utf-8"
    )
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1

    captured = capsys.readouterr()
    assert "cannot read acknowledgements" in captured.err
    assert "acknowledged" not in captured.out


def test_an_acknowledgement_on_a_closed_task_still_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acknowledgement on a closed task still counts.

    The record binds the commit, not the task's state — an
    acknowledgement written while the task was open still acknowledges
    its hit after the task is abandoned.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head) == 0
    assert main(["abandon", "--task", "CR-001", "--reason", "dropped"]) == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    assert "acknowledged by an-operator" in capsys.readouterr().out


def test_a_repository_with_no_journal_behaves_as_without_acknowledgements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a repository with no journal behaves as without acknowledgements.

    No project, no journal: the read is skipped outright and the run is
    exactly a run with no acknowledgements — the hit unmarked, exit 1.
    A `--task` there names records that cannot be read, and says so.
    """

    repo = tmp_path / "plain"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    (repo / "readme.md").write_text("hello\n", encoding="utf-8")
    base = _commit_all(repo, "base")
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1

    captured = capsys.readouterr()
    assert captured.out == (
        "leak-scan: possible leaks in added content (file: what matched): "
        "secret.py: github-token\n"
    )
    assert "cannot read acknowledgements" not in captured.err

    assert (
        main(["leak-scan", "--base", base, "--commit", head, "--task", "CR-001"]) == 1
    )
    captured = capsys.readouterr()
    assert "cannot read acknowledgements" in captured.err
    assert captured.out == (
        "leak-scan: possible leaks in added content (file: what matched): "
        "secret.py: github-token\n"
    )


# -- the match is the scan's own naming ---------------------------------------


def test_an_acknowledgement_bound_to_the_hit_acknowledges_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acknowledgement bound to the hit acknowledges it.

    Commit, file and identification all three equal the hit's — the
    record counts, the hit prints marked and the run exits 0.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head) == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    assert (
        "secret.py: github-token (acknowledged by an-operator: reviewed, not a leak)"
        in capsys.readouterr().out
    )


def test_a_markers_number_identifies_a_marker_hit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a marker's number identifies a marker hit.

    The record carries `marker` 1 and the hit's identification is
    `private-marker #1` on the same commit and file — acknowledged.
    """

    repo = _repo(tmp_path, monkeypatch, markers=(_MARKER,))
    base = _head(repo)
    head = _add_file(repo, "host.py", f"HOST = '{_MARKER}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert (
        _acknowledge(base, head, file="host.py", marker=1, reason="internal host") == 0
    )
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    output = capsys.readouterr().out
    assert (
        "host.py: private-marker #1 "
        "(acknowledged by an-operator: internal host)" in output
    )
    assert _MARKER not in output


def test_a_record_on_another_commit_acknowledges_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a record on another commit acknowledges nothing.

    The record names the hit's file and identification, but its
    `commit` is the base, not the candidate: an acknowledgement lives
    and dies with the exact commit it was given on.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(
        repo, "CR-001", base, "secret.py", "verified on the wrong commit"
    )
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1

    output = capsys.readouterr().out
    assert "secret.py: github-token" in output
    assert "acknowledged" not in output


def test_a_file_spelled_differently_acknowledges_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a file spelled differently acknowledges nothing.

    The record's `file` is `./secret.py` where the scan prints
    `secret.py`: same file, a spelling the scan never printed, and
    string equality is the whole match — no normalisation.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(
        repo, "CR-001", head, "./secret.py", "verified under another spelling"
    )
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1

    output = capsys.readouterr().out
    assert "secret.py: github-token" in output
    assert "acknowledged" not in output


def test_an_identification_that_is_not_the_hits_acknowledges_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an identification that is not the hit's acknowledges nothing.

    Same commit and file, a different signature id — and the
    renumbered-marker case: the record holds `marker` 1 where the
    renumbered list now prints the hit `private-marker #2`. Both show
    the hit unacknowledged again.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(
        repo,
        "CR-001",
        head,
        "secret.py",
        "verified a different signature",
        signature="aws-access-key-id",
    )
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1

    output = capsys.readouterr().out
    assert "secret.py: github-token" in output
    assert "acknowledged" not in output

    # The renumbered-marker case: the marker list gained an entry ahead
    # of the recorded one, so the hit now prints #2 while the record
    # holds 1.
    repo2 = _repo(
        tmp_path / "two",
        monkeypatch,
        markers=("other.example.invalid", _MARKER),
    )
    base2 = _head(repo2)
    head2 = _add_file(repo2, "host.py", f"HOST = '{_MARKER}'\n")
    _open()  # CR-001 in the second repo
    _write_acknowledgement(
        repo2, "CR-001", head2, "host.py", "recorded before renumbering", marker=1
    )
    capsys.readouterr()

    assert main(["leak-scan", "--base", base2, "--commit", head2]) == 1

    captured = capsys.readouterr()
    assert "host.py: private-marker #2" in captured.out
    assert "acknowledged" not in captured.out
    assert _MARKER not in captured.out
    assert _MARKER not in captured.err


def test_the_earliest_matching_record_marks_the_hit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the earliest matching record marks the hit.

    Two records name the same hit — one on CR-001, one on CR-002: the
    mark names the record that comes earlier in journal order.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()  # CR-001
    _open()  # CR-002
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(repo, "CR-002", head, "secret.py", "later in journal order")
    _write_acknowledgement(repo, "CR-001", head, "secret.py", "first in journal order")
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    output = capsys.readouterr().out
    assert "acknowledged by an-operator: first in journal order" in output
    assert "later in journal order" not in output


# -- every hit printed, the exit on the unacknowledged ------------------------


def test_an_acknowledged_hit_prints_marked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acknowledged hit prints marked.

    The hit's own entry carries the mark — acknowledged, by whom, and
    the reason — appended to the file and identification it always
    printed.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head) == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    assert capsys.readouterr().out == (
        "leak-scan: possible leaks in added content (file: what matched): "
        "secret.py: github-token "
        "(acknowledged by an-operator: reviewed, not a leak)\n"
    )


def test_every_hit_still_prints_in_todays_order_and_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every hit still prints in today's order and form.

    Two hits in scan order, only the second acknowledged: both entries
    print in the order and form they always had, the acknowledged one
    carrying the mark, and the run still exits 1.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    _add_file(repo, "aaa.py", f"key = '{_AWS_KEY}'\n")
    head = _add_file(repo, "zzz.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head, file="zzz.py") == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1

    assert capsys.readouterr().out == (
        "leak-scan: possible leaks in added content (file: what matched): "
        "aaa.py: aws-access-key-id, zzz.py: github-token "
        "(acknowledged by an-operator: reviewed, not a leak)\n"
    )


def test_the_mark_is_escaped_where_it_could_forge_a_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the mark is escaped where it could forge a line.

    A `recorded_by` carrying a newline and a line separator reaches the
    mark — the write rules never constrained it — and prints as its
    escapes: it can neither add a line nor reorder what prints.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "op\nera\u202etor")
    assert _acknowledge(base, head) == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    captured = capsys.readouterr()
    assert "op\nera\u202etor" not in captured.out
    assert "op\nera\u202etor" not in captured.err
    assert "op\\nera\\u202etor" in captured.out


def test_the_matched_text_is_never_printed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the matched text is never printed.

    The mark carries who acknowledged and why — the record holds the
    identification, never the matched text, so the token appears on
    neither stream.
    """

    repo = _repo(tmp_path, monkeypatch, markers=(_MARKER,))
    base = _head(repo)
    _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    head = _add_file(repo, "host.py", f"HOST = '{_MARKER}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head, file="secret.py") == 0
    assert _acknowledge(base, head, file="host.py", marker=1) == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    captured = capsys.readouterr()
    assert _GITHUB_TOKEN not in captured.out
    assert _GITHUB_TOKEN not in captured.err
    assert _MARKER not in captured.out
    assert _MARKER not in captured.err


def test_every_hit_acknowledged_exits_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every hit acknowledged exits 0."""

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    head = _add_file(repo, "other.py", f"key = '{_AWS_KEY}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head, file="secret.py") == 0
    assert _acknowledge(base, head, file="other.py", signature="aws-access-key-id") == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    output = capsys.readouterr().out
    assert "secret.py: github-token (acknowledged" in output
    assert "other.py: aws-access-key-id (acknowledged" in output


def test_any_unacknowledged_hit_exits_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: any unacknowledged hit exits 1.

    One hit acknowledged, one not: the run exits 1 on the one nobody
    acknowledged.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    head = _add_file(repo, "other.py", f"key = '{_AWS_KEY}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head, file="secret.py") == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1

    output = capsys.readouterr().out
    assert "other.py: aws-access-key-id" in output
    assert "other.py: aws-access-key-id (acknowledged" not in output


def test_a_clean_scan_is_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a clean scan is unchanged.

    Nothing the journal holds — an acknowledgement included — changes a
    run whose scan reports no hits.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "module.py", "def add(a, b):\n    return a + b\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    # A record bound to the candidate that names no hit still changes
    # nothing: there is no hit for it to mark.
    _write_acknowledgement(repo, "CR-001", head, "secret.py", "names no hit here")
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    assert capsys.readouterr().out == (
        "leak-scan: no known leak signatures in added content\n"
    )


def test_a_run_with_no_acknowledgement_is_byte_for_byte_todays(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a run with no acknowledgement is byte for byte today's."""

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1

    captured = capsys.readouterr()
    assert captured.out == (
        "leak-scan: possible leaks in added content (file: what matched): "
        "secret.py: github-token\n"
    )
    assert captured.err == (
        "(best-effort: a hit is not proof of a leak and a clean run is not "
        "proof of safety — see ADR-0005)\n"
    )


def test_the_merge_boundarys_line_carries_no_mark_yet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the merge boundary's line carries no mark yet.

    The same acknowledged hit, seen by the gate: its line is the file
    and identification the standalone command gives, with no mark —
    marking the boundary is a later task.
    """

    from test_gate import _approve, _gate_repo, _implement, _run

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert (
        _acknowledge(
            base,
            head,
            task="CR-001",
            file="src/module.py",
            signature="aws-access-key-id",
        )
        == 0
    )

    passed, output = _run(repo, head, base, head)

    gate_line = next(line for line in output.splitlines() if line.startswith("WARN:"))
    assert passed, output
    assert gate_line == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/module.py: aws-access-key-id"
    )
