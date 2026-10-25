"""The acknowledgement mark identifies a self-acknowledgement.

ADR-0021 decision 5, release-audit finding AUD-commands-3: where an
acknowledgement's acknowledging party is a declared author or committer,
the mark `leak-scan` and the gate's advisory line print says
`self-acknowledged` — the term `status` already uses, derived through
the shared writer lookup and comparison: the gate over the candidate
range, `leak-scan` over the commit it scans. Any other acknowledgement,
and a check git cannot answer, prints exactly as today.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

import agentmarshal.cli as cli_module
from agentmarshal.cli import main
from agentmarshal.journal import gate as gate_module
from test_gate import _approve, _gate_repo, _implement, _run
from test_leak_scan_acknowledgements import (
    _GITHUB_TOKEN,
    _add_file,
    _git,
    _head,
    _open,
    _repo,
    _write_acknowledgement,
)

_WRITER_EMAIL = "test@example.invalid"


@pytest.fixture(autouse=True)
def _isolated_actor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _commit_with_author(
    repo: Path, message: str, author_name: str, author_email: str
) -> str:
    """Commit staged work: ``-c`` supplies the committer, the env the author."""
    _git(repo, "add", "-A")
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            f"user.email={_WRITER_EMAIL}",
            "commit",
            "--quiet",
            "-m",
            message,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
        },
    )
    return _git(repo, "rev-parse", "HEAD")


def test_the_standalone_command_marks_a_self_acknowledgement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the standalone command marks a self-acknowledgement.

    The recorder names the scanned commit's own declared email — a
    writer acknowledging its own hit — and the mark says so in the term
    `status` uses.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", _WRITER_EMAIL)
    _write_acknowledgement(repo, "CR-001", head, "secret.py", "reviewed my own hit")
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    assert capsys.readouterr().out == (
        "leak-scan: possible leaks in added content (file: what matched): "
        "secret.py: github-token "
        f"(self-acknowledged by {_WRITER_EMAIL}: reviewed my own hit)\n"
    )


def test_the_gate_marks_a_self_acknowledgement_over_the_candidate_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the gate marks a self-acknowledgement over the candidate range.

    The recorder names the candidate's own declared email: the advisory
    line's mark says `self-acknowledged` while the warning stays
    advisory and the gate still passes.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/leak.py", f"key = '{_GITHUB_TOKEN}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "worker@test.invalid")
    _write_acknowledgement(repo, "CR-001", head, "src/leak.py", "reviewed my own hit")
    capsys.readouterr()

    passed, output = _run(repo, head, base, head)

    gate_line = next(line for line in output.splitlines() if line.startswith("WARN:"))
    assert passed, output
    assert gate_line == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/leak.py: github-token "
        "(self-acknowledged by worker@test.invalid: reviewed my own hit)"
    )


def test_the_commits_committer_marks_a_self_acknowledgement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the commit's committer marks a self-acknowledgement.

    The commit's declared author is someone else; the recorder names
    its committer. The comparison holds against both declared writers,
    so the mark says `self-acknowledged`.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    (repo / "secret.py").write_text(f"key = '{_GITHUB_TOKEN}'\n", encoding="utf-8")
    head = _commit_with_author(repo, "add secret.py", "Other", "other@example.invalid")
    _open()
    # The committer is Test <test@example.invalid>, the author Other:
    # naming the committer still marks the acknowledgement its own.
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", _WRITER_EMAIL)
    _write_acknowledgement(repo, "CR-001", head, "secret.py", "committed it myself")
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    output = capsys.readouterr().out
    assert (
        f"secret.py: github-token "
        f"(self-acknowledged by {_WRITER_EMAIL}: committed it myself)" in output
    )


def test_a_declared_actors_resolved_identity_marks_a_self_acknowledgement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a declared actor's resolved identity marks a self-acknowledgement.

    `recorded_by` is `dev` — no declared writer is named `dev` — but
    the actors table resolves `dev` to the commit's declared email: the
    resolved identities, not only the recorded name, are compared.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["actors"] = {"dev": {"git_identities": [_WRITER_EMAIL]}}
    project_file.write_text(json.dumps(data) + "\n", encoding="utf-8")
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "dev")
    _write_acknowledgement(repo, "CR-001", head, "secret.py", "reviewed my own hit")
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    assert (
        "secret.py: github-token "
        "(self-acknowledged by dev: reviewed my own hit)" in capsys.readouterr().out
    )


def test_a_writer_of_an_earlier_range_commit_marks_at_the_gate_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a writer of an earlier range commit marks at the gate alone.

    The hit lands in an earlier commit of the range, the candidate tip
    is another writer's and the acknowledgement binds the tip: the gate
    compares over the whole range and marks `self-acknowledged`, while
    `leak-scan` — comparing against the scanned commit alone — does
    not. The journal holds no candidate base for the command to
    rebuild the range from.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    (repo / "src").mkdir()
    (repo / "src" / "leak.py").write_text(
        f"key = '{_GITHUB_TOKEN}'\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=Earlier",
        "-c",
        "user.email=earlier@test.invalid",
        "commit",
        "--quiet",
        "-m",
        "earlier work",
    )
    head = _implement(repo, "src/more.py", "x = 1\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "earlier@test.invalid")
    _write_acknowledgement(
        repo, "CR-001", head, "src/leak.py", "reviewed my earlier work"
    )
    capsys.readouterr()

    passed, output = _run(repo, head, base, head)

    gate_line = next(line for line in output.splitlines() if line.startswith("WARN:"))
    assert passed, output
    assert (
        "src/leak.py: github-token "
        "(self-acknowledged by earlier@test.invalid: reviewed my earlier work)"
        in gate_line
    )

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0
    out = capsys.readouterr().out
    assert "(acknowledged by earlier@test.invalid: reviewed my earlier work)" in out
    assert "self-acknowledged" not in out


def test_an_acknowledgement_by_another_party_prints_unmarked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acknowledgement by another party prints unmarked.

    The recorder is no declared writer: the standalone command and the
    gate's line print the mark exactly as today — `acknowledged by`,
    never `self-acknowledged`.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/leak.py", f"key = '{_GITHUB_TOKEN}'\n")
    _approve(repo, head)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    _write_acknowledgement(repo, "CR-001", head, "src/leak.py", "reviewed, not a leak")
    capsys.readouterr()

    passed, output = _run(repo, head, base, head)

    gate_line = next(line for line in output.splitlines() if line.startswith("WARN:"))
    assert passed, output
    assert gate_line == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/leak.py: github-token "
        "(acknowledged by an-operator: reviewed, not a leak)"
    )

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0
    assert capsys.readouterr().out == (
        "leak-scan: possible leaks in added content (file: what matched): "
        "src/leak.py: github-token "
        "(acknowledged by an-operator: reviewed, not a leak)\n"
    )


def test_a_check_git_cannot_answer_marks_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a check git cannot answer marks nothing.

    The writer lookup fails for both surfaces — the gate's range lookup
    raises `GateError`, as it does on a git failure, and the command's
    commit lookup answers `None` — so a record that would mark as the
    writer's own prints the mark it always prints; `status` alone
    reports the check did not run.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/leak.py", f"key = '{_GITHUB_TOKEN}'\n")
    # The recorder names a real writer; only the unanswered lookup
    # stands between the record and the mark — and nothing is marked.
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "worker@test.invalid")
    _write_acknowledgement(repo, "CR-001", head, "src/leak.py", "reviewed")
    capsys.readouterr()

    def _unanswered(*args: object) -> tuple[set[str], set[str]]:
        raise gate_module.GateError("git log failed")

    monkeypatch.setattr(gate_module, "_range_writer_identities", _unanswered)

    # review_required=False with no review record leaves the verdict
    # block's writer_identities empty, so the advisory's lazy lookup is
    # the call that runs — and the GateError it raises is the lookup
    # failure the mark must survive.
    report = gate_module.run_gate(
        repo, "CR-001", head, base, head, review_required=False
    )
    passed, output = report.passed, "\n".join(report.lines)

    gate_line = next(line for line in output.splitlines() if line.startswith("WARN:"))
    assert passed, output
    assert gate_line == (
        "WARN: possible leak in candidate additions (advisory, not blocking): "
        "src/leak.py: github-token "
        "(acknowledged by worker@test.invalid: reviewed)"
    )

    monkeypatch.setattr(cli_module, "declared_commit_writers", lambda *args: None)
    assert main(["leak-scan", "--base", base, "--commit", head]) == 0
    assert capsys.readouterr().out == (
        "leak-scan: possible leaks in added content (file: what matched): "
        "src/leak.py: github-token "
        "(acknowledged by worker@test.invalid: reviewed)\n"
    )


def test_the_writer_check_folds_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the writer check folds case.

    `recorded_by` spells the commit's declared email in upper case —
    the same case-insensitive comparison `status` makes — and the mark
    still says `self-acknowledged`.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "secret.py", f"key = '{_GITHUB_TOKEN}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "TEST@EXAMPLE.INVALID")
    _write_acknowledgement(repo, "CR-001", head, "secret.py", "reviewed my own hit")
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 0

    assert (
        "secret.py: github-token "
        "(self-acknowledged by TEST@EXAMPLE.INVALID: reviewed my own hit)"
        in capsys.readouterr().out
    )
