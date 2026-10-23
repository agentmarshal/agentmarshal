"""`complete`'s dispositions for the review's advisory findings.

ADR-0016 decision 1: for the review the gate passed on — the approving
latest review of the candidate's commit, or the non-approving one an
acceptance covered — `complete` takes a `--disposition` for each of its
advisory findings, recorded in `advisory_dispositions` through
`create_completed_record`'s parameter (CR-175's field), and refuses
before writing `completed` when any lacks one. `complete --findings`
takes no dispositions. The gate's report carries that review's id —
set by the same code that decides the verdict check — and `complete`
reads the advisory findings from the record carrying it among the
records the gate evaluated, so a review appended after the gate ran
cannot change which are owed.
"""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.complete import LifecycleError, record_commit_completion
from agentmarshal.journal.gate import GateReport, run_gate
from agentmarshal.journal.records import read_records

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]
_REVIEWER_EMAIL = "reviewer@test.invalid"


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=repo, check=True, capture_output=True, encoding="utf-8"
    )
    return result.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Loop task", "--scope", "src/"]) == 0
    base = _commit_all(repo, "open task")
    return repo, base


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _implement(repo: Path) -> str:
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    return _commit_all(repo, "implement")


def _review(
    head: str,
    verdict: str = "approved",
    *,
    findings: tuple[str, ...] = (),
    advisory: tuple[str, ...] = (),
) -> None:
    arguments = [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        head,
        "--verdict",
        verdict,
        "--role",
        "qa",
        "--vendor",
        "test",
        "--model",
        "test-model",
        "--email",
        _REVIEWER_EMAIL,
    ]
    for finding in findings:
        arguments.extend(["--finding", finding])
    for finding in advisory:
        arguments.extend(["--advisory-finding", finding])
    assert main(arguments) == 0


def _complete(head: str, base: str, *extra: str) -> int:
    return main(
        [
            "complete",
            "--task",
            "CR-001",
            "--commit",
            head,
            "--base",
            base,
            "--pipeline-sha",
            head,
            *extra,
        ]
    )


def _no_completed_record(repo: Path) -> bool:
    return all(
        record["record_type"] != "completed"
        for record in read_records(_journal(repo), "CR-001")
    )


def test_a_completion_answers_each_advisory_finding_of_the_approving_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a completion answers each advisory finding of the
    approving review."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1", "F-2", "F-3"))
    capsys.readouterr()

    assert (
        _complete(
            head,
            base,
            "--disposition",
            "F-1=fixed",
            "--disposition",
            "F-2=deferred:not this round",
            "--disposition",
            "F-3=rejected:not a defect",
        )
        == 0
    )
    assert "completed" in capsys.readouterr().out

    completed = read_records(_journal(repo), "CR-001")[-1]
    assert completed["record_type"] == "completed"
    assert completed["completed_commit"] == head
    assert completed["advisory_dispositions"] == {
        "F-1": {"disposition": "fixed"},
        "F-2": {"disposition": "deferred", "reason": "not this round"},
        "F-3": {"disposition": "rejected", "reason": "not a defect"},
    }
    assert completed["schema"] == 7


def test_a_deferred_disposition_may_name_a_follow_up_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a deferred disposition may name a follow-up task."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert (
        _complete(
            head,
            base,
            "--disposition",
            "F-1=deferred:not this round",
            "--follow-up",
            "F-1=CR-007",
        )
        == 0
    )

    completed = read_records(_journal(repo), "CR-001")[-1]
    assert completed["advisory_dispositions"] == {
        "F-1": {
            "disposition": "deferred",
            "reason": "not this round",
            "follow_up": "CR-007",
        }
    }


def test_a_reason_is_everything_after_the_first_colon(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a reason is everything after the first colon."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert _complete(head, base, "--disposition", "F-1=rejected:not:a:defect") == 0

    completed = read_records(_journal(repo), "CR-001")[-1]
    assert completed["advisory_dispositions"] == {
        "F-1": {"disposition": "rejected", "reason": "not:a:defect"}
    }


def test_a_fixed_disposition_may_carry_a_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a fixed disposition may carry a reason."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert _complete(head, base, "--disposition", "F-1=fixed:already done") == 0

    completed = read_records(_journal(repo), "CR-001")[-1]
    assert completed["advisory_dispositions"] == {
        "F-1": {"disposition": "fixed", "reason": "already done"}
    }


def test_dispositions_answer_the_non_approving_review_an_acceptance_covered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the review the gate passed on may be a non-approving
    review an acceptance covered."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(
        head,
        "changes_required",
        findings=("F-1",),
        advisory=("A-1",),
    )
    assert (
        main(
            [
                "accept",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--by",
                "operator@test.invalid",
                "--reason",
                "The review loop did not converge",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert _complete(head, base, "--disposition", "A-1=fixed") == 0

    output = capsys.readouterr().out
    assert "accepted over findings F-1" in output
    completed = read_records(_journal(repo), "CR-001")[-1]
    assert completed["advisory_dispositions"] == {"A-1": {"disposition": "fixed"}}


def test_a_review_with_no_advisory_findings_completes_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a review with no advisory findings completes as before."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head)
    capsys.readouterr()

    assert _complete(head, base) == 0
    assert "completed" in capsys.readouterr().out

    completed = read_records(_journal(repo), "CR-001")[-1]
    assert "advisory_dispositions" not in completed
    assert completed["schema"] == 3


def test_an_unanswered_advisory_finding_refuses_naming_every_unanswered_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unanswered advisory finding refuses, naming every
    unanswered id."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1", "F-2", "F-3"))
    capsys.readouterr()

    assert _complete(head, base) == 1
    error = capsys.readouterr().err
    assert "F-1" in error and "F-2" in error and "F-3" in error
    assert "--disposition" in error
    assert _no_completed_record(repo)

    assert _complete(head, base, "--disposition", "F-1=fixed") == 1
    error = capsys.readouterr().err
    assert "F-2" in error and "F-3" in error
    assert _no_completed_record(repo)


def test_a_disposition_for_an_id_the_review_did_not_raise_refuses_naming_the_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a disposition for an id the review did not raise
    refuses, naming the id."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert (
        _complete(
            head,
            base,
            "--disposition",
            "F-1=fixed",
            "--disposition",
            "F-9=fixed",
        )
        == 1
    )

    error = capsys.readouterr().err
    assert "F-9" in error
    assert _no_completed_record(repo)


def test_a_follow_up_for_an_id_the_review_did_not_raise_refuses_naming_the_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a follow-up for an id the review did not raise refuses,
    naming the id."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert (
        _complete(
            head,
            base,
            "--disposition",
            "F-1=fixed",
            "--follow-up",
            "F-9=CR-007",
        )
        == 1
    )

    error = capsys.readouterr().err
    assert "F-9" in error
    assert _no_completed_record(repo)


@pytest.mark.parametrize("word", ["deferred", "rejected"])
def test_a_deferred_or_rejected_without_a_reason_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    word: str,
) -> None:
    """Scenario: a deferred or rejected without a reason refuses."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert _complete(head, base, "--disposition", f"F-1={word}") == 1

    error = capsys.readouterr().err
    assert "F-1" in error
    assert "--disposition" in error
    assert _no_completed_record(repo)


@pytest.mark.parametrize("word", ["fixed", "rejected:not a defect"])
def test_a_follow_up_on_a_disposition_other_than_deferred_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    word: str,
) -> None:
    """Scenario: a follow-up on a disposition other than deferred
    refuses."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert (
        _complete(
            head, base, "--disposition", f"F-1={word}", "--follow-up", "F-1=CR-007"
        )
        == 1
    )

    error = capsys.readouterr().err
    assert "F-1" in error
    assert "--follow-up" in error
    assert _no_completed_record(repo)


def test_a_disposition_word_outside_the_vocabulary_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value the record rules refuse is refused naming the
    flag — a disposition word outside the vocabulary."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert _complete(head, base, "--disposition", "F-1=wontfix") == 1

    error = capsys.readouterr().err
    assert "F-1" in error
    assert "--disposition" in error
    assert _no_completed_record(repo)


def test_a_reason_carrying_a_forgeable_character_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value the record rules refuse is refused naming the
    flag — a reason carrying a forgeable character."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert _complete(head, base, "--disposition", "F-1=deferred:no\nreason") == 1

    error = capsys.readouterr().err
    assert "F-1" in error
    assert "--disposition" in error
    assert _no_completed_record(repo)


def test_a_follow_up_that_is_not_a_task_id_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value the record rules refuse is refused naming the
    flag — a follow-up that is not a task id."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert (
        _complete(
            head,
            base,
            "--disposition",
            "F-1=deferred:not this round",
            "--follow-up",
            "F-1=TASK-7",
        )
        == 1
    )

    error = capsys.readouterr().err
    assert "F-1" in error
    assert "--follow-up" in error
    assert _no_completed_record(repo)


def test_a_malformed_disposition_flag_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed flag refuses — a disposition with no `=`."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert _complete(head, base, "--disposition", "F-1") == 1

    error = capsys.readouterr().err
    assert "--disposition" in error
    assert _no_completed_record(repo)


def test_a_malformed_follow_up_flag_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed flag refuses — a follow-up with no `=`."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert (
        _complete(head, base, "--disposition", "F-1=fixed", "--follow-up", "F-1") == 1
    )

    error = capsys.readouterr().err
    assert "--follow-up" in error
    assert _no_completed_record(repo)


def test_a_flag_repeated_for_one_id_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a flag repeated for one id refuses."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    capsys.readouterr()

    assert (
        _complete(
            head,
            base,
            "--disposition",
            "F-1=fixed",
            "--disposition",
            "F-1=rejected:not a defect",
        )
        == 1
    )

    error = capsys.readouterr().err
    assert "F-1" in error
    assert _no_completed_record(repo)


def test_the_disposition_flags_are_refused_on_the_findings_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the disposition flags are refused on the findings
    lane."""

    repo, _base = _repo(tmp_path, monkeypatch)
    capsys.readouterr()

    assert (
        main(
            [
                "complete",
                "--task",
                "CR-001",
                "--findings",
                "--disposition",
                "F-1=fixed",
            ]
        )
        == 1
    )
    assert "takes no dispositions" in capsys.readouterr().err
    assert _no_completed_record(repo)

    assert (
        main(
            [
                "complete",
                "--task",
                "CR-001",
                "--findings",
                "--follow-up",
                "F-1=CR-007",
            ]
        )
        == 1
    )
    assert "takes no dispositions" in capsys.readouterr().err
    assert _no_completed_record(repo)


def test_a_findings_completion_without_flags_is_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a findings completion without flags is unchanged."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    _git(repo, "config", "user.name", "Recorder")
    _git(repo, "config", "user.email", "recorder@test.invalid")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "researcher")
    assert main(["init"]) == 0
    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["actors"] = {"researcher": {"git_identities": ["recorder@test.invalid"]}}
    project_path.write_text(json.dumps(project), encoding="utf-8")
    assert main(["open", "--title", "Research"]) == 0
    journal = _journal(repo)
    artifact = repo / "evidence" / "result.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("conclusion\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert (
        main(
            [
                "finding",
                "--task",
                "CR-001",
                "--summary",
                "The conclusion",
                "--artifact",
                f"evidence/result.md={digest}",
            ]
        )
        == 0
    )
    finding_id = str(read_records(journal, "CR-001")[-1]["id"])
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--reviewed-finding",
                finding_id,
                "--verdict",
                "approved",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                _REVIEWER_EMAIL,
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert main(["complete", "--task", "CR-001", "--findings"]) == 0

    completed = read_records(journal, "CR-001")[-1]
    assert completed["completed_finding"] == finding_id
    assert "advisory_dispositions" not in completed


def test_the_sidecar_lane_takes_and_requires_dispositions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The sidecar's advisory `complete` is the same command: the review
    the gate passed on lives in the sidecar journal, and its advisory
    findings take the same dispositions."""

    host = tmp_path / "host"
    host.mkdir()
    _git(host, "init", "--quiet", "-b", "master")
    (host / "app.txt").write_text("one\n", encoding="utf-8")
    base = _commit_all(host, "base")
    (host / "app.txt").write_text("two\n", encoding="utf-8")
    head = _commit_all(host, "work")
    sidecar = tmp_path / "sidecar"
    sidecar.mkdir()
    _git(sidecar, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    assert main(["open", "--title", "Sidecar gate", "--scope", "app.txt"]) == 0
    _review(head, advisory=("A-1",))
    capsys.readouterr()

    assert _complete(head, base) == 1
    assert "A-1" in capsys.readouterr().err

    assert _complete(head, base, "--disposition", "A-1=fixed") == 0

    completed = read_records(sidecar / ".agentmarshal" / "journal", "CR-001")[-1]
    assert completed["advisory_dispositions"] == {"A-1": {"disposition": "fixed"}}


def test_an_advisory_finding_id_carrying_an_equals_sign_is_answered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """CR192-001: the value splits against the advisory ids of the
    review the gate passed on — the longest such id it starts with
    followed by `=`, so an advisory id may itself carry `=`."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F=1", "F=1=deep"))
    capsys.readouterr()

    assert (
        _complete(
            head,
            base,
            "--disposition",
            "F=1=fixed",
            "--disposition",
            "F=1=deep=rejected:measured noise",
        )
        == 0
    )

    completed = read_records(_journal(repo), "CR-001")[-1]
    assert completed["advisory_dispositions"] == {
        "F=1": {"disposition": "fixed"},
        "F=1=deep": {"disposition": "rejected", "reason": "measured noise"},
    }


def test_an_advisory_id_named_follow_up_reports_its_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """CR192-002: a refusal names the flag the value came through —
    carried with the parsed argument, never read off the refusal's
    text — so an advisory id called `follow_up` keeps a bad
    `--disposition` reported as a `--disposition` error."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("follow_up",))
    capsys.readouterr()

    assert _complete(head, base, "--disposition", "follow_up=bogus") == 1

    error = capsys.readouterr().err
    assert "--disposition" in error
    assert "--follow-up" not in error
    assert "follow_up" in error
    assert _no_completed_record(repo)


def test_the_gate_report_carries_the_id_of_the_approving_review_it_passed_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the gate's report carries the id of the approving
    review it passed on."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    review_id = str(read_records(_journal(repo), "CR-001")[-1]["id"])
    capsys.readouterr()

    report = run_gate(repo, "CR-001", head, base, head)

    assert report.passed
    assert report.resolved_review == review_id


def test_the_gate_report_carries_the_id_of_the_review_an_acceptance_covered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the gate's report carries the id of the review an
    acceptance covered."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, "changes_required", findings=("F-1",), advisory=("A-1",))
    review_id = str(read_records(_journal(repo), "CR-001")[-1]["id"])
    assert (
        main(
            [
                "accept",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--by",
                "operator@test.invalid",
                "--reason",
                "The review loop did not converge",
            ]
        )
        == 0
    )
    capsys.readouterr()

    report = run_gate(repo, "CR-001", head, base, head)

    assert report.passed
    assert report.resolved_review == review_id


def test_the_gate_report_carries_no_review_id_when_it_passed_on_no_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the gate's report carries no review id when it passed
    on no review."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    capsys.readouterr()

    report = run_gate(repo, "CR-001", head, base, head, review_required=False)

    assert report.passed
    assert report.review_not_examined
    assert report.resolved_review is None


def test_an_appended_review_cannot_change_which_advisory_findings_are_owed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a review appended after the gate ran cannot change
    which advisory findings are owed — the command end to end."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1", "F-2"))

    # A concurrent process of the same user appends a newer review of the
    # same commit — carrying no advisory findings — between the gate's
    # verdict check and the disposition check `complete` runs after it.
    def gate_then_append(*args: Any, **kwargs: Any) -> GateReport:
        report = run_gate(*args, **kwargs)
        _review(head)
        return report

    monkeypatch.setattr("agentmarshal.journal.complete.run_gate", gate_then_append)
    capsys.readouterr()

    assert _complete(head, base) == 1

    error = capsys.readouterr().err
    assert "F-1" in error and "F-2" in error
    assert _no_completed_record(repo)


def test_an_advisory_id_of_an_appended_review_refuses_naming_the_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an advisory id raised only by a review appended after
    the gate refuses, naming the id."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1",))
    report = run_gate(repo, "CR-001", head, base, head)
    assert report.passed
    _review(head, advisory=("F-9",))
    capsys.readouterr()

    with pytest.raises(LifecycleError) as excinfo:
        record_commit_completion(
            _journal(repo),
            "CR-001",
            report.resolved_commit,
            resolved_review=report.resolved_review,
            dispositions=["F-1=fixed", "F-9=fixed"],
        )

    assert "F-9" in str(excinfo.value)
    assert _no_completed_record(repo)


def test_a_completion_after_an_appended_review_writes_its_dispositions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a completion after an appended review writes the
    passed-on review's dispositions."""

    repo, base = _repo(tmp_path, monkeypatch)
    head = _implement(repo)
    _review(head, advisory=("F-1", "F-2"))
    report = run_gate(repo, "CR-001", head, base, head)
    assert report.passed
    _review(head, advisory=("F-9",))
    capsys.readouterr()

    record_path = record_commit_completion(
        _journal(repo),
        "CR-001",
        report.resolved_commit,
        resolved_review=report.resolved_review,
        dispositions=["F-1=fixed", "F-2=deferred:not this round"],
    )

    assert record_path.exists()
    completed = read_records(_journal(repo), "CR-001")[-1]
    assert completed["record_type"] == "completed"
    assert completed["advisory_dispositions"] == {
        "F-1": {"disposition": "fixed"},
        "F-2": {"disposition": "deferred", "reason": "not this round"},
    }
