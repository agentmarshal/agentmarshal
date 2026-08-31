"""Tests for the merge gate."""

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.gate import GateError, markers_from_tree, run_gate
from agentmarshal.journal.records import (
    create_acceptance_record,
    create_completed_record,
    create_session_record,
    write_record,
)

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]
_REVIEWER_EMAIL = "reviewer@test.invalid"


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _gate_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scope: list[str]
) -> tuple[Path, str]:
    """Initialized repo with an opened task committed on master."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    arguments = ["open", "--title", "Gate task"]
    for entry in scope:
        arguments.extend(["--scope", entry])
    assert main(arguments) == 0
    base = _commit_all(repo, "open task")
    return repo, base


def _implement(repo: Path, path: str, content: str = "code\n") -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _commit_all(repo, "implement")


def _approve(repo: Path, commit: str, email: str = _REVIEWER_EMAIL) -> None:
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                commit,
                "--verdict",
                "approved",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                email,
            ]
        )
        == 0
    )


def _require_changes(
    repo: Path,
    commit: str,
    *findings: str,
    email: str = _REVIEWER_EMAIL,
) -> None:
    arguments = [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        commit,
        "--verdict",
        "changes_required",
        "--role",
        "qa",
        "--vendor",
        "test",
        "--model",
        "test-model",
        "--email",
        email,
    ]
    for finding in findings:
        arguments.extend(["--finding", finding])
    assert main(arguments) == 0


def _accept(
    repo: Path, commit: str, accepted_by: str = "operator@example.invalid"
) -> None:
    assert (
        main(
            [
                "accept",
                "--task",
                "CR-001",
                "--commit",
                commit,
                "--by",
                accepted_by,
                "--reason",
                "The review loop did not converge",
            ]
        )
        == 0
    )


def _run(
    repo: Path, commit: str, base: str, pipeline_sha: str | None
) -> tuple[bool, str]:
    report = run_gate(repo, "CR-001", commit, base, pipeline_sha)
    return report.passed, "\n".join(report.lines)


def test_gate_passes_a_clean_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    # The review record stays uncommitted in the journal working tree:
    # a review never has to be part of the very diff it attests.
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert output.count("FAIL") == 0


def test_gate_refuses_path_outside_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "outside/module.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "outside contract scope" in output


def test_gate_refuses_undeclared_journal_change_in_mixed_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    # A journal document under the task dir that the base contract scope
    # does not list, bundled with the in-scope code change.
    (repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "extra.md").write_text(
        "undeclared\n", encoding="utf-8"
    )
    head = _commit_all(repo, "mixed candidate with undeclared journal change")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "outside contract scope" in output


def test_gate_refuses_missing_and_stale_reviews(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")

    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "no review record" in output

    _approve(repo, head)
    stale_head = _commit_all(repo, "record review")

    # The review targets the previous head, not the candidate head.
    passed, output = _run(repo, stale_head, base, stale_head)
    assert not passed
    assert "no review record" in output


def test_gate_refuses_non_approved_latest_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)
    _require_changes(repo, head, "F-001")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert f"FAIL: latest review of {head[:12]} is approved" in output


def test_gate_passes_valid_acceptance_without_reporting_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001", "F-002")
    _accept(repo, head, accepted_by="operator@example.invalid")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert (
        "PASS: accepted over findings F-001, F-002 by "
        "operator@example.invalid; not an approving review"
    ) in output
    assert f"latest review of {head[:12]} is approved" not in output


@pytest.mark.parametrize(
    ("review_findings", "acceptance_findings"),
    [
        (("F-001", "F-002"), ["F-001"]),
        (("F-001",), ["F-001", "F-002"]),
    ],
)
def test_gate_re_derives_acceptance_findings_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    review_findings: tuple[str, ...],
    acceptance_findings: list[str],
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, *review_findings)
    journal = repo / ".agentmarshal" / "journal"
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            head,
            "operator@example.invalid",
            acceptance_findings,
            "Crafted without the accept command's validation",
        ),
    )

    passed, output = _run(repo, head, base, head)

    assert not passed
    # The acceptance exists but does not cover what is outstanding, and the
    # refusal says so rather than reporting only a missing approval.
    assert f"FAIL: acceptance of {head[:12]} does not cover the latest" in output
    assert "accepted over findings" not in output


def test_gate_refuses_acceptance_made_stale_by_a_later_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _accept(repo, head)
    _require_changes(repo, head, "F-001", "F-002")

    passed, output = _run(repo, head, base, head)

    assert not passed
    # The acceptance exists but does not cover what is outstanding, and the
    # refusal says so rather than reporting only a missing approval.
    assert f"FAIL: acceptance of {head[:12]} does not cover the latest" in output
    assert "accepted over findings" not in output


def test_gate_refuses_acceptance_for_a_different_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    journal = repo / ".agentmarshal" / "journal"
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            "a" * 40,
            "operator@example.invalid",
            ["F-001"],
            "Acceptance of another commit",
        ),
    )

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert f"FAIL: latest review of {head[:12]} is approved" in output


def test_gate_still_refuses_dependent_reviewer_with_valid_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001", email="worker@test.invalid")
    _accept(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "accepted over findings" in output
    assert "declared reviewer identity differs" in output


def test_gate_refuses_dependent_reviewer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head, email="worker@test.invalid")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "declared reviewer identity differs" in output


def test_gate_refuses_missing_or_wrong_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, None)
    assert not passed
    assert "attestation" in output

    passed, output = _run(repo, head, base, "0" * 40)
    assert not passed
    assert "attestation" in output


def test_gate_ci_required_delegates_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)

    # No pipeline_sha at all, yet ci-required delegates attestation:
    report = run_gate(repo, "CR-001", head, base, None, attestation="ci-required")

    assert report.passed, "\n".join(report.lines)
    assert "delegated to the provider's required checks" in "\n".join(report.lines)


def test_gate_ci_required_still_enforces_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")  # no review recorded

    report = run_gate(repo, "CR-001", head, base, None, attestation="ci-required")

    assert not report.passed
    assert "no review record" in "\n".join(report.lines)


def test_gate_ci_required_still_enforces_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "outside/bad.py")
    _approve(repo, head)

    report = run_gate(repo, "CR-001", head, base, None, attestation="ci-required")

    assert not report.passed
    assert "outside contract scope" in "\n".join(report.lines)


def test_gate_unknown_attestation_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")

    with pytest.raises(GateError, match="unknown attestation mode"):
        run_gate(repo, "CR-001", head, base, head, attestation="bogus")


def test_gate_journal_only_lane_needs_no_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    note = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "note.md"
    note.write_text("journal-only change\n", encoding="utf-8")
    head = _commit_all(repo, "journal-only")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "deterministic lane" in output


def test_gate_detects_record_path_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])

    # A second task opened on master after the candidate forks: its
    # record path exists on the target tip but not at the merge base.
    assert main(["open", "--title", "Other task"]) == 0
    other_records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-002" / "records"
    record_file = next(other_records.glob("*-opened.json"))
    record_relative = record_file.relative_to(repo)
    record_content = record_file.read_text(encoding="utf-8")
    _commit_all(repo, "open other task on master")

    # The candidate, forked before that, independently creates the same
    # record path (journal-only, so only the collision check applies).
    _git(repo, "switch", "--quiet", "-c", "candidate", base)
    (repo / record_relative).parent.mkdir(parents=True)
    (repo / record_relative).write_text(record_content, encoding="utf-8")
    contract_source = (
        repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    )
    contract_target = (
        repo / ".agentmarshal" / "journal" / "tasks" / "CR-002" / "contract.md"
    )
    contract_target.write_text(
        contract_source.read_text(encoding="utf-8").replace("CR-001", "CR-002"),
        encoding="utf-8",
    )
    head = _commit_all(repo, "independently open other task")

    passed, output = _run(repo, head, "master", head)

    assert not passed
    assert "already exist" in output


def _candidate_head(repo: Path, branch: str, base: str, mutate: object) -> str:
    """Commit a candidate on its own branch, evaluate from a clean master."""

    _git(repo, "switch", "--quiet", "-c", branch, base)
    mutate()  # type: ignore[operator]
    head = _commit_all(repo, branch)
    _git(repo, "switch", "--quiet", "master")
    return head


def test_gate_refuses_record_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    opened = next(records.glob("*-opened.json"))

    def modify() -> None:
        opened.write_text(opened.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    head = _candidate_head(repo, "tamperer", base, modify)
    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "append-only" in output

    def delete() -> None:
        _git(repo, "rm", "--quiet", str(opened.relative_to(repo)))

    head = _candidate_head(repo, "deleter", base, delete)
    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "append-only" in output


def test_gate_refuses_record_rename_out_of_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    opened = next(records.glob("*-opened.json"))

    def rename_out() -> None:
        _git(
            repo,
            "mv",
            str(opened.relative_to(repo)),
            ".agentmarshal/journal/tasks/CR-001/evacuated.json",
        )

    head = _candidate_head(repo, "evacuator", base, rename_out)
    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "append-only" in output


def test_gate_refuses_case_variant_reviewer_email(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head, email="Worker@Test.INVALID")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "declared reviewer identity differs" in output


def test_gate_refuses_invalid_added_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    opened = next(records.glob("*-opened.json"))
    crafted_name = "01" + "A" * 24 + "-opened.json"

    def add_malformed() -> None:
        (records / crafted_name).write_text("not json\n", encoding="utf-8")

    head = _candidate_head(repo, "malformed", base, add_malformed)
    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "invalid added records" in output

    original = opened.read_text(encoding="utf-8")

    def add_mismatched() -> None:
        (records / crafted_name).write_text(
            original.replace("CR-001", "CR-002"), encoding="utf-8"
        )

    head = _candidate_head(repo, "mismatched", base, add_mismatched)
    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "does not match its directory" in output


def test_gate_reports_malformed_base_contract_without_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    valid_contract = contract.read_text(encoding="utf-8")

    # The base tree carries a malformed contract; the candidate restores
    # a valid one in the working tree, so the failure is reached only at
    # the base-tree scope check, not at working-tree status loading.
    contract.write_text("no header here\n", encoding="utf-8")
    base = _commit_all(repo, "corrupt contract on base")
    _implement(repo, "src/module.py")
    contract.write_text(valid_contract, encoding="utf-8")
    head = _commit_all(repo, "restore valid contract in working tree")
    capsys.readouterr()

    assert (
        main(
            [
                "gate",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--base",
                base,
                "--pipeline-sha",
                head,
            ]
        )
        == 1
    )

    error_output = capsys.readouterr().err
    assert "contract in the base tree is invalid" in error_output
    assert "Traceback" not in error_output


def test_gate_refuses_second_opened_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    opened = next(records.glob("*-opened.json"))
    original = opened.read_text(encoding="utf-8")

    # A second, individually valid opened record: passes isolation checks
    # but makes the task unreadable after merge.
    def add_second_opened() -> None:
        (records / ("01" + "B" * 24 + "-opened.json")).write_text(
            original, encoding="utf-8"
        )

    head = _candidate_head(repo, "double-open", base, add_second_opened)
    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "multiple opened records" in output


def test_gate_refuses_non_utf8_git_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import os

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    src_bytes = os.fsencode(repo / "src")
    os.makedirs(src_bytes, exist_ok=True)
    # A genuinely non-UTF-8 filename (raw 0xFF byte), created at the OS
    # level so git stores and emits the raw bytes.
    bad_path = src_bytes + b"/\xff.py"
    with open(bad_path, "wb") as bad_file:
        bad_file.write(b"code\n")
    head = _commit_all(repo, "non-utf8 path")
    capsys.readouterr()

    assert (
        main(
            [
                "gate",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--base",
                base,
                "--pipeline-sha",
                head,
            ]
        )
        == 1
    )

    error_output = capsys.readouterr().err
    assert "non-UTF-8" in error_output
    assert "Traceback" not in error_output


def test_gate_requires_contract_in_base_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    base = _commit_all(repo, "seed without journal")
    assert main(["open", "--title", "Gate task"]) == 0
    head = _implement(repo, "src/module.py")

    with pytest.raises(GateError, match="base tree"):
        run_gate(repo, "CR-001", head, base, head)


def test_gate_allows_completion_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A completion transaction appends a terminal record to a task that is
    # open at the base; the open->done transition must pass, not trip the
    # base-state check.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    _git(repo, "switch", "--quiet", "-c", "completion", base)
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    head = _commit_all(repo, "complete CR-001")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "task CR-001 is not closed at base" in output


def test_gate_refuses_candidate_on_a_task_closed_at_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Once a task is closed on the base tree, no non-measurement candidate
    # may merge against it (a session-only append is the exception below).
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "after-close", closed_base)
    head = _implement(repo, "src/more.py")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_allows_session_only_append_to_closed_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A task closed at base still admits measurements: a journal-only
    # candidate whose added records are all session records accrues
    # economics after the terminal record (ADR-0005 Decision 3).
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "measure", closed_base)
    write_record(
        journal,
        "CR-001",
        create_session_record(
            "CR-001", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "record session for CR-001")

    passed, output = _run(repo, head, closed_base, head)

    assert passed, output
    assert "measurements-only append to a task closed at base" in output
    assert output.count("FAIL") == 0


def test_gate_refuses_measurements_lane_with_another_tasks_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The measurements exception is per-task: a session record belonging to
    # a different task must not authorize a change against a closed one.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "cross-task", closed_base)
    write_record(
        journal,
        "CR-002",
        create_session_record(
            "CR-002", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "record a CR-002 session while gating closed CR-001")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_refuses_artifact_only_append_to_closed_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The measurements lane requires at least one session record: a
    # journal candidate adding only a non-record document to a closed task
    # is not a measurement and is still refused by the base-state check.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "note", closed_base)
    (journal / "tasks" / "CR-001" / "note.md").write_text("late\n", encoding="utf-8")
    head = _commit_all(repo, "add a note to a closed task")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_passes_approved_review_with_advisory_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Advisory findings never block a merge: an approved review carrying
    # them still passes the gate's review check.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                head,
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
                "--advisory-finding",
                "F1",
                "--advisory-finding",
                "F2",
            ]
        )
        == 0
    )

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert output.count("FAIL") == 0


def test_gate_measurements_lane_allows_a_new_supplementary_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A session record plus a genuinely new supplementary artifact under
    # the task directory is a valid measurements append to a closed task.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "measure-artifact", closed_base)
    artifact = journal / "tasks" / "CR-001" / "artifacts" / "prompt.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("prompt\n", encoding="utf-8")
    write_record(
        journal,
        "CR-001",
        create_session_record(
            "CR-001", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "record session and a new artifact")

    passed, output = _run(repo, head, closed_base, head)

    assert passed, output
    assert "measurements-only append to a task closed at base" in output


def test_gate_measurements_lane_refuses_modifying_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Appended evidence must never authorize a mutation of an existing
    # file: a session record bundled with a contract.md change on a closed
    # task is refused because the change is not strictly additive.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "tamper-contract", closed_base)
    contract = journal / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8") + "\nmutated\n", encoding="utf-8"
    )
    write_record(
        journal,
        "CR-001",
        create_session_record(
            "CR-001", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "session plus a contract mutation")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_measurements_lane_refuses_modifying_existing_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Modifying an existing artifact (not adding one) is not additive and
    # is refused even alongside a session record.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    artifact = journal / "tasks" / "CR-001" / "artifacts" / "prompt.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("original\n", encoding="utf-8")
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 with an artifact")

    _git(repo, "switch", "--quiet", "-c", "mutate-artifact", closed_base)
    artifact.write_text("changed\n", encoding="utf-8")
    write_record(
        journal,
        "CR-001",
        create_session_record(
            "CR-001", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "session plus an artifact mutation")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_warns_on_leak_without_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    # An added line trips the built-in secret signatures.
    head = _implement(repo, "src/module.py", "aws_key = 'AKIAIOSFODNN7EXAMPLE'\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    # Advisory: the gate warns but still passes, and never emits a FAIL.
    assert passed, output
    assert output.count("FAIL") == 0
    assert "WARN: possible leak in candidate additions" in output
    assert "aws-access-key-id" in output


def test_gate_leak_scan_is_clean_for_benign_additions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", "def add(a, b):\n    return a + b\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "WARN:" not in output


def test_gate_leak_scan_uses_configured_private_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": ["internal.example.invalid"]}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # Commit the config into the base so the marker only trips on the
    # candidate's own added content, not on the config declaration itself.
    base = _commit_all(repo, "configure private markers")
    head = _implement(repo, "src/host.py", "HOST = 'internal.example.invalid'\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "WARN: possible leak in candidate additions" in output
    assert "private-marker" in output


def test_gate_leak_scan_reads_markers_from_base_not_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/", ".agentmarshal/"])
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": ["internal.example.invalid"]}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    base = _commit_all(repo, "configure private markers")

    # The candidate tries to weaken its own scan: drop the marker from config
    # and, in the same change, add content the base-configured marker catches.
    data["leak_scan"] = {"private_markers": []}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    src = repo / "src"
    src.mkdir(exist_ok=True)
    (src / "host.py").write_text(
        "HOST = 'internal.example.invalid'\n", encoding="utf-8"
    )
    head = _commit_all(repo, "weaken config and add marked content")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    # Config comes from the base tree, so the candidate cannot suppress the
    # warning by editing its own project.json.
    assert passed, output
    assert "WARN: possible leak in candidate additions" in output
    assert "private-marker" in output


def test_gate_leak_scan_scans_binary_marked_file_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A candidate marks its file 'binary' in .gitattributes; without --text
    # git would emit "Binary files differ" and hide the secret. --text forces
    # content, so the added secret is still scanned.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/", ".gitattributes"])
    (repo / ".gitattributes").write_text("src/secret.py binary\n", encoding="utf-8")
    src = repo / "src"
    src.mkdir(exist_ok=True)
    (src / "secret.py").write_text("key = 'AKIAIOSFODNN7EXAMPLE'\n", encoding="utf-8")
    head = _commit_all(repo, "binary-marked secret")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "WARN: possible leak in candidate additions" in output
    assert "aws-access-key-id" in output


def test_markers_from_tree_absent_project_json_yields_no_markers(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    (repo / "file.txt").write_text("x\n", encoding="utf-8")
    # A commit that deliberately has no .agentmarshal/project.json.
    ref = _commit_all(repo, "no project file")

    assert markers_from_tree(repo, ref) == ()


def test_markers_from_tree_bad_ref_raises_rather_than_dropping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    # An unknown ref is a real failure, surfaced — not silently "no markers".
    with pytest.raises(GateError):
        markers_from_tree(repo, "definitely-not-a-ref")


def test_gate_leak_scan_degrades_to_warning_on_bad_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": "not-a-list"}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    base = _commit_all(repo, "malformed leak_scan config")
    head = _implement(repo, "src/module.py", "code\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    # A malformed advisory config never blocks a merge: it degrades to a warn.
    assert passed, output
    assert output.count("FAIL") == 0
    assert "WARN: leak-scan skipped" in output
