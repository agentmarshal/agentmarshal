"""Tests for the self-acceptance mark on the gate and report surfaces.

ADR-0007 decision 4 marks a self-acceptance on every surface that reports
the task; decision 5 has ``report`` say how the completed record's own
binding actually closed (release-audit findings AUD-gate-journal-5 and
-4).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.gate import run_gate
from agentmarshal.journal.records import (
    create_acceptance_record,
    create_completed_record,
    create_finding_record,
    create_reopened_record,
    create_review_record,
    write_record,
)
from agentmarshal.journal.report import build_report, format_report
from test_gate import _accept, _gate_repo, _implement, _require_changes
from test_journal import initialize_status_repo


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    A finding record must name its recorder, and CI has neither
    AGENTMARSHAL_ACTOR nor a git identity — so every test sets one the way
    tests/test_status_view.py does, rather than inheriting whatever the
    runner happens to provide.
    """

    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "tester")


def _report_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """An initialized repo with an opened task, and its journal root."""

    repo = tmp_path / "repo"
    journal_root = initialize_status_repo(repo)
    monkeypatch.chdir(repo)
    assert main(["open", "--title", "Task"]) == 0
    return repo, journal_root


def _commit(repo: Path, name: str, *, committer: tuple[str, str] | None = None) -> str:
    """Commit a file as Test <test@example.invalid> and return its id.

    ``committer`` — a ``(name, email)`` pair — overrides the commit's
    committer identity through ``GIT_COMMITTER_*``, so a test can stand
    a commit whose committer differs from its author.
    """

    (repo / name).write_text(f"{name}\n", encoding="utf-8")
    env = dict(os.environ)
    if committer is not None:
        env["GIT_COMMITTER_NAME"], env["GIT_COMMITTER_EMAIL"] = committer
    subprocess.run(["git", "add", name], cwd=repo, check=True)
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
        env=env,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _implement_as(repo: Path, path: str, name: str, email: str) -> str:
    """Commit ``path`` with ``name <email>`` as author and committer."""

    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("code\n", encoding="utf-8")
    subprocess.run(["git", "add", path], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            f"user.name={name}",
            "-c",
            f"user.email={email}",
            "commit",
            "--quiet",
            "-m",
            path,
        ],
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


def _implement_latin1_author(repo: Path, head: str) -> str:
    """HEAD rewritten with an author name that is not valid UTF-8.

    ``git hash-object`` stores the commit text as given — where
    ``commit-tree`` would recode the ident — so a latin-1 author name
    reaches the object with no encoding header, and ``git log`` hands
    ``%an`` back as bytes no UTF-8 decode survives. The new commit
    carries the same tree over ``head`` as parent, so the candidate
    range keeps its diff.
    """

    tree = subprocess.run(
        ["git", "rev-parse", f"{head}^{{tree}}"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    commit_text = (
        f"tree {tree}\nparent {head}\n".encode("ascii")
        + b"author Andr\xe9 <worker@test.invalid> 1792878322 +0000\n"
        b"committer Committer <committer@test.invalid> 1792878322 +0000\n"
        b"\nimplement\n"
    )
    rewritten = subprocess.run(
        ["git", "hash-object", "-w", "-t", "commit", "--stdin"],
        cwd=repo,
        check=True,
        capture_output=True,
        input=commit_text,
    ).stdout.strip()
    subprocess.run(
        ["git", "reset", "--quiet", "--hard", rewritten.decode("ascii")],
        cwd=repo,
        check=True,
    )
    return rewritten.decode("ascii")


def _implement_distinct_committer(repo: Path, path: str) -> str:
    """A candidate commit authored by Worker but committed by Committer.

    ``GIT_COMMITTER_*`` overrides only the committer half, so the
    commit's declared author and committer identities differ — the case
    where the writer set must still find the committing party.
    """

    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("code\n", encoding="utf-8")
    subprocess.run(["git", "add", path], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Worker",
            "-c",
            "user.email=worker@test.invalid",
            "commit",
            "--quiet",
            "-m",
            "implement",
        ],
        cwd=repo,
        check=True,
        env={
            **os.environ,
            "GIT_COMMITTER_NAME": "Committer",
            "GIT_COMMITTER_EMAIL": "committer@test.invalid",
        },
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _review(commit: str, verdict: str, *findings: str) -> dict[str, object]:
    return create_review_record(
        "CR-001",
        "test",
        commit,
        verdict,
        "qa",
        "test",
        "model",
        "reviewer@test.invalid",
        list(findings),
    )


def _report_line(capsys: pytest.CaptureFixture[str], task_id: str) -> str:
    """Run ``report`` and return the task's line."""

    assert main(["report"]) == 0
    (line,) = (
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith(f"{task_id}\t")
    )
    return line


@pytest.mark.parametrize(
    "party", ["worker@test.invalid", "Worker@Test.Invalid", "Worker"]
)
def test_the_gates_acceptance_line_marks_a_self_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, party: str
) -> None:
    """Scenario: the gate's acceptance line marks a self-acceptance.

    ``Worker`` alone names the writer — the shared comparison reads the
    candidate range's declared names and emails alike, so a name-valued
    accepting party marks as readily as an address.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _accept(repo, head, accepted_by=party)

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert report.passed, output
    assert (
        f"PASS: accepted over findings F-001 by {party} (self-accepted: "
        "accepting party is a declared author or committer); "
        "not an approving review"
    ) in output


@pytest.mark.parametrize("party", ["committer@test.invalid", "Committer"])
def test_the_gates_acceptance_line_marks_a_committer_self_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, party: str
) -> None:
    """Scenario: the gate's acceptance line marks a self-acceptance.

    The accepting party is the commit's committer, not its author — by
    email and by name alike, since the declared writers are the names
    and emails of both.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement_distinct_committer(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _accept(repo, head, accepted_by=party)

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert report.passed, output
    assert (
        f"PASS: accepted over findings F-001 by {party} (self-accepted: "
        "accepting party is a declared author or committer); "
        "not an approving review"
    ) in output


def test_the_gate_runs_over_an_author_name_that_is_not_utf8(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-UTF-8 author name cannot fail the gate's writer read.

    The range's ``git log`` is read as bytes and split on NUL: names
    decode lossily where emails decode as strictly as before, so a
    commit whose author name is not UTF-8 keeps the gate running — and
    the surviving email half of the identity still earns the mark. The
    range's other commit is written by another identity, so only the
    latin-1 commit's own email can supply it.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement_latin1_author(
        repo, _implement_as(repo, "src/module.py", "Other", "other@test.invalid")
    )
    _require_changes(repo, head, "F-001")
    _accept(repo, head, accepted_by="worker@test.invalid")

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert report.passed, output
    assert (
        "PASS: accepted over findings F-001 by worker@test.invalid "
        "(self-accepted: accepting party is a declared author or "
        "committer); not an approving review"
    ) in output


def test_an_acceptance_by_another_party_prints_unmarked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an acceptance by another party prints unmarked."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _accept(repo, head, accepted_by="operator@example.invalid")

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert report.passed, output
    assert (
        "PASS: accepted over findings F-001 by operator@example.invalid; "
        "not an approving review"
    ) in output
    assert "self-accepted" not in output

    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", head))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )


def test_a_writer_of_an_earlier_range_commit_is_marked_by_the_gate_alone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a writer of an earlier range commit is marked by the gate alone.

    The documented asymmetry the requirement states: the gate compares
    the accepting party against the declared writers of every commit in
    the candidate range, where ``report`` and ``status`` can read only
    the accepted commit's — the journal holds no candidate base — so a
    party who wrote an earlier commit of the range but not its tip
    earns the mark at the gate and nowhere else.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _implement_as(repo, "src/first.py", "Alice", "alice@test.invalid")
    head = _implement_as(repo, "src/second.py", "Bob", "bob@test.invalid")
    _require_changes(repo, head, "F-001")
    _accept(repo, head, accepted_by="alice@test.invalid")

    report = run_gate(repo, "CR-001", head, base, head)

    output = "\n".join(report.lines)
    assert report.passed, output
    assert (
        "PASS: accepted over findings F-001 by alice@test.invalid "
        "(self-accepted: accepting party is a declared author or "
        "committer); not an approving review"
    ) in output

    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", head))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )


@pytest.mark.parametrize("party", ["test@example.invalid", "Test@Example.Invalid"])
def test_reports_task_line_marks_a_self_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    party: str,
) -> None:
    """Scenario: report's task line marks a self-acceptance."""

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(repo, "tracked.py")
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record("CR-001", "test", commit, party, ["F-1"], "accepted"),
    )
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", commit))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0"
        "\tdecision=accepted-over-findings\tself-accepted"
    )


@pytest.mark.parametrize("party", ["committer@test.invalid", "Committer"])
def test_reports_task_line_marks_a_committer_self_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    party: str,
) -> None:
    """Scenario: report's task line marks a self-acceptance.

    The accepted commit's author is Test; the accepting party is its
    committer — by email and by name alike, since the declared writers
    are the names and emails of both.
    """

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(
        repo, "tracked.py", committer=("Committer", "committer@test.invalid")
    )
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record("CR-001", "test", commit, party, ["F-1"], "accepted"),
    )
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", commit))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0"
        "\tdecision=accepted-over-findings\tself-accepted"
    )


def test_report_and_status_keep_the_mark_over_a_non_utf8_author_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A non-UTF-8 author name cannot lose the mark on report or status.

    The accepted commit's writer read decodes names with ``replace`` and
    emails strictly — the same split the gate's range lookup makes — so
    a commit whose author name is not UTF-8 keeps the mark on every
    surface, earned by the surviving email half of the identity.
    """

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _implement_latin1_author(repo, _commit(repo, "tracked.py"))
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001", "test", commit, "worker@test.invalid", ["F-1"], "accepted"
        ),
    )
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", commit))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0"
        "\tdecision=accepted-over-findings\tself-accepted"
    )

    assert main(["status", "CR-001"]) == 0
    assert "self-accepted" in capsys.readouterr().out


def test_reports_task_line_prints_unmarked_when_the_check_cannot_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: report's task line prints unmarked when the check cannot run."""

    repo, journal = _report_repo(tmp_path, monkeypatch)
    # The accepted commit exists nowhere in the journal's repository —
    # the line prints as for any other acceptance; status alone says
    # the check could not run.
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001", "test", "a" * 40, "worker@test.invalid", ["F-1"], "accepted"
        ),
    )
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\topen\treviews=0\ttokens=0\tdecision=accepted-over-findings"
    )

    # And when no repository answers for the journal at all.
    (repo / ".agentmarshal" / "project.json").unlink()
    report = build_report(journal)
    assert format_report(report)[0] == (
        "CR-001\topen\treviews=0\ttokens=0\tdecision=accepted-over-findings"
    )


def test_a_commit_approved_after_an_earlier_commits_acceptance_reports_approved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a commit approved after an earlier commit's acceptance reports approved

    The earlier commit's acceptance is even a self-acceptance by party —
    nothing it carries may leak onto the commit that closed on approval.
    """

    _repo, journal = _report_repo(tmp_path, monkeypatch)
    write_record(journal, "CR-001", _review("a" * 40, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            "a" * 40,
            "test@example.invalid",
            ["F-1"],
            "accepted",
        ),
    )
    write_record(journal, "CR-001", _review("b" * 40, "approved"))
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", "b" * 40))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=2\ttokens=0\tdecision=approved"
    )


def test_a_commit_completed_over_findings_reports_accepted_over_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a commit completed over findings reports accepted-over-findings."""

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(repo, "tracked.py")
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            commit,
            "operator@example.invalid",
            ["F-1"],
            "accepted",
        ),
    )
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", commit))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )


def test_a_finding_completed_over_findings_reports_accepted_over_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a finding completed over findings reports accepted-over-findings.

    The accepting party is a declared writer of a real commit — so the
    absent mark is the finding binding's own doing: an
    ``accepted_finding`` carries no ``accepted_commit`` whose writers
    could be compared, not merely a party that matched no writer.
    """

    repo, journal = _report_repo(tmp_path, monkeypatch)
    _commit(repo, "tracked.py")
    finding = write_record(
        journal,
        "CR-001",
        create_finding_record(
            "CR-001",
            "test",
            "A finding",
            [{"ref": "evidence/result.md", "hash": "b" * 64}],
        ),
    ).name.split("-")[0]
    write_record(
        journal,
        "CR-001",
        create_review_record(
            "CR-001",
            "test",
            None,
            "changes_required",
            "qa",
            "test",
            "model",
            "reviewer@test.invalid",
            ["F-1"],
            reviewed_finding=finding,
        ),
    )
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            None,
            "test@example.invalid",
            ["F-1"],
            "accepted",
            accepted_finding=finding,
        ),
    )
    write_record(
        journal,
        "CR-001",
        create_completed_record("CR-001", "test", None, completed_finding=finding),
    )
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )


def test_a_commit_approved_after_its_own_acceptance_reports_approved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a commit approved after its own acceptance reports approved.

    review(changes_required) → acceptance → review(approved) → completed,
    all on one commit: the completed commit's latest review decides, so
    the task reports closed on approval — `accepted-over-findings` is for
    a completion whose commit's latest review is non-approving and an
    acceptance covers it. The standing self-acceptance earns no mark.
    """

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(repo, "tracked.py")
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            commit,
            "test@example.invalid",
            ["F-1"],
            "accepted",
        ),
    )
    write_record(journal, "CR-001", _review(commit, "approved"))
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", commit))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\tdone\treviews=2\ttokens=0\tdecision=approved"
    )


def test_an_acceptance_bound_to_another_commit_leaves_no_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an acceptance bound to another commit leaves no decision."""

    _repo, journal = _report_repo(tmp_path, monkeypatch)
    write_record(journal, "CR-001", _review("a" * 40, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record("CR-001", "test", "a" * 40, "op", ["F-1"], "accepted"),
    )
    write_record(journal, "CR-001", _review("b" * 40, "changes_required", "F-2"))
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", "b" * 40))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == ("CR-001\tdone\treviews=2\ttokens=0")


def test_a_review_written_after_the_completion_does_not_change_its_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a review written after the completion does not change its decision.

    review(changes_required) → acceptance → completed → reopened →
    review(approved), all on one commit: the completed record's decision
    reads only the records written before it, so the approval the
    reopened task earned cannot rewrite a completion that closed over
    findings — and the task, open again, keeps the completed record's
    report of how it closed.
    """

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(repo, "tracked.py")
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record("CR-001", "test", commit, "op", ["F-1"], "accepted"),
    )
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", commit))
    write_record(journal, "CR-001", create_reopened_record("CR-001", "test", "work"))
    write_record(journal, "CR-001", _review(commit, "approved"))
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\topen\treviews=2\ttokens=0\tdecision=accepted-over-findings"
    )


def test_a_task_with_no_completed_record_keeps_todays_decision_rule(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a task with no completed record keeps today's decision rule."""

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(repo, "tracked.py")
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record("CR-001", "test", commit, "op", ["F-1"], "accepted"),
    )
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\topen\treviews=1\ttokens=0\tdecision=accepted-over-findings"
    )


def test_a_task_with_no_completed_record_marks_a_self_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: report's task line marks a self-acceptance.

    The no-`completed`-record branch applies the mark to the latest
    findings-carrying acceptance it reports: a self-accepting party
    earns `self-accepted` there exactly as on the completed lane.
    """

    repo, journal = _report_repo(tmp_path, monkeypatch)
    commit = _commit(repo, "tracked.py")
    write_record(journal, "CR-001", _review(commit, "changes_required", "F-1"))
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001", "test", commit, "test@example.invalid", ["F-1"], "accepted"
        ),
    )
    capsys.readouterr()

    assert _report_line(capsys, "CR-001") == (
        "CR-001\topen\treviews=1\ttokens=0"
        "\tdecision=accepted-over-findings\tself-accepted"
    )
