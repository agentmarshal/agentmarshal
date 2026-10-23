"""The gate marks acknowledged hits on its advisory leak-scan line.

ADR-0021 decisions 2 and 3: the gate is one of the surfaces an
acknowledgement prints on — a hit the task's `acknowledgement`
records bound to the candidate's commit name prints marked,
acknowledged, by whom and why — the same mark `leak-scan` builds
for the same hit. The line's bound is unchanged — at most twenty
hits, then "and N more not shown" — and an acknowledgement neither
removes a hit nor changes which are shown or their order. The line
stays a warning and blocks nothing.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_acknowledgement_record,
    write_record,
)
from test_gate import _approve, _commit_all, _gate_repo, _implement, _run

_GITHUB_TOKEN = f"ghp_{'A1' * 18}"
_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
_MARKER = "internal.example.invalid"


@pytest.fixture(autouse=True)
def _isolated_actor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _acknowledge(
    base: str,
    head: str,
    *,
    task: str = "CR-001",
    file: str = "src/module.py",
    signature: str = "aws-access-key-id",
    reason: str = "reviewed, not a leak",
) -> int:
    return main(
        [
            "acknowledge",
            "--task",
            task,
            "--base",
            base,
            "--commit",
            head,
            "--file",
            file,
            "--signature",
            signature,
            "--reason",
            reason,
        ]
    )


def _write_acknowledgement(
    repo: Path,
    task: str,
    commit: str,
    file: str,
    reason: str,
    *,
    signature: str | None = "aws-access-key-id",
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


def _leak_line(output: str) -> str:
    return next(
        line for line in output.splitlines() if line.startswith("WARN: possible leak")
    )


def _configured_markers(repo: Path, markers: list[str]) -> str:
    """Write private markers into the project file and commit them to base."""

    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": markers}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return _commit_all(repo, "configure private markers")


def test_an_acknowledged_hit_is_marked_on_the_gates_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an acknowledged hit is marked on the gate's line.

    The record bound to the candidate's commit names the file exactly
    as the scan prints it and the hit's identification — the hit's
    entry on the line gains the mark, who acknowledged it and why.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head) == 0

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/module.py: aws-access-key-id "
        "(acknowledged by an-operator: reviewed, not a leak)"
    )


def test_the_mark_is_the_one_the_standalone_command_prints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the mark is the one the standalone command prints.

    The same acknowledged hit, seen by the boundary's line and by
    `leak-scan`: the mark the two surfaces print is the same text —
    acknowledged, by whom and why.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head) == 0

    passed, gate_output = _run(repo, head, base, head)
    capsys.readouterr()
    assert main(["leak-scan", "--base", base, "--commit", head]) == 0
    standalone = capsys.readouterr()

    mark = "(acknowledged by an-operator: reviewed, not a leak)"
    assert passed, gate_output
    assert mark in _leak_line(gate_output)
    assert mark in standalone.out


def test_a_marked_hit_adds_no_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a marked hit adds no violation.

    The line stays a warning: the gate passes the acknowledged
    candidate exactly as it did the unacknowledged one — the scan
    decides nothing with or without the record.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    assert _acknowledge(base, head) == 0

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert not any(line.startswith("FAIL:") for line in output.splitlines())


def test_the_bound_is_unchanged_and_the_unshown_stay_unmarked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the bound is unchanged and the unshown stay unmarked.

    Twenty-one hits and an acknowledgement for each of the first and
    the last: the line still shows twenty and says how many it did not
    — the first carries its mark, the last is part of the count and
    shows none.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    for index in range(21):
        head = _implement(repo, f"src/secret{index:02}.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(repo, "CR-001", head, "src/secret00.py", "shown")
    _write_acknowledgement(repo, "CR-001", head, "src/secret20.py", "unshown")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    expected = ", ".join(
        ["src/secret00.py: aws-access-key-id (acknowledged by an-operator: shown)"]
        + [f"src/secret{index:02}.py: aws-access-key-id" for index in range(1, 20)]
    )
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        + expected
        + ", and 1 more not shown"
    )
    assert "src/secret20.py" not in _leak_line(output)
    assert "unshown" not in _leak_line(output)


def test_an_acknowledgement_changes_neither_the_hits_shown_nor_their_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an acknowledgement changes neither the hits shown nor their order.

    Two hits in scan order, the second acknowledged: both entries
    print where they always did, the acknowledged one marked, the
    other untouched.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _implement(repo, "src/aaa.py", f"key = '{_AWS_KEY}'\n")
    head = _implement(repo, "src/zzz.py", f"key = '{_GITHUB_TOKEN}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(
        repo,
        "CR-001",
        head,
        "src/zzz.py",
        "reviewed, not a leak",
        signature="github-token",
    )

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/aaa.py: aws-access-key-id, src/zzz.py: github-token "
        "(acknowledged by an-operator: reviewed, not a leak)"
    )


def test_an_acknowledgement_bound_to_another_commit_marks_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an acknowledgement bound to another commit marks nothing.

    The record names the hit's file and identification, but its
    `commit` is the base, not the candidate: an acknowledgement lives
    and dies with the exact commit it was given on.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(
        repo, "CR-001", base, "src/module.py", "verified on the wrong commit"
    )

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/module.py: aws-access-key-id"
    )


def test_an_acknowledgement_of_another_task_marks_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an acknowledgement of another task marks nothing.

    The record bound to the candidate's commit sits on CR-002; the
    gate reads the records of the task it runs on, so CR-001's line
    shows the hit unmarked.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    assert main(["open", "--title", "Other task"]) == 0  # CR-002
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(repo, "CR-002", head, "src/module.py", "not this task")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/module.py: aws-access-key-id"
    )


def test_a_file_spelled_differently_marks_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a file spelled differently marks nothing.

    The record's `file` is `./src/module.py` where the scan prints
    `src/module.py`: string equality is the whole match, and a
    spelling the scan never printed marks nothing.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(repo, "CR-001", head, "./src/module.py", "another spelling")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/module.py: aws-access-key-id"
    )


def test_an_identification_that_is_not_the_hits_marks_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an identification that is not the hit's marks nothing.

    Same commit and file, a different signature id: the record's
    `github-token` does not equal the hit's `aws-access-key-id`, so
    the hit shows unacknowledged.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(
        repo,
        "CR-001",
        head,
        "src/module.py",
        "verified a different signature",
        signature="github-token",
    )

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/module.py: aws-access-key-id"
    )


def test_the_earliest_matching_record_marks_the_hit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the earliest matching record marks the hit.

    Two records of the task name the same hit: the mark names the one
    earlier in journal order.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(repo, "CR-001", head, "src/module.py", "first")
    _write_acknowledgement(repo, "CR-001", head, "src/module.py", "second")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    gate_line = _leak_line(output)
    assert "(acknowledged by an-operator: first)" in gate_line
    assert "second" not in gate_line


def test_a_recorder_named_the_secret_is_masked_in_the_mark(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a recorder named the secret is masked in the mark.

    A recorder's name is the operator's own text: an actor named
    exactly the configured marker reaches the mark, which is masked
    the way every printed name is — the marker's value appears
    nowhere.
    """

    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    base = _configured_markers(repo, [_MARKER])
    head = _implement(repo, "src/host.py", f"HOST = '{_MARKER}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", _MARKER)
    _write_acknowledgement(
        repo, "CR-001", head, "src/host.py", "reviewed", signature=None, marker=1
    )

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/host.py: private-marker #1 "
        "(acknowledged by [masked: private-marker]: reviewed)"
    )
    assert _MARKER not in output


def test_the_mark_is_escaped_where_it_could_forge_a_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the mark is escaped where it could forge a line.

    A `recorded_by` carrying a newline and a line separator reaches
    the mark — the write rules never constrained it — and prints as
    its escapes: it can neither add a line nor reorder what prints.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "op\nera\u202etor")
    _write_acknowledgement(repo, "CR-001", head, "src/module.py", "reviewed")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "op\nera\u202etor" not in output
    assert "op\\nera\\u202etor" in _leak_line(output)


def test_a_candidate_with_no_acknowledgement_is_byte_for_byte_todays(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a candidate with no acknowledgement is byte for byte today's.

    Nothing the journal holds changes the line when no record names
    the candidate's commit: the hits print exactly as before, unmarked.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", f"key = '{_AWS_KEY}'\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert _leak_line(output) == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/module.py: aws-access-key-id"
    )
