"""Research-finding records and their no-candidate gate lane."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.gate import run_findings_gate, run_gate
from agentmarshal.journal.records import (
    JournalRecordError,
    create_completed_record,
    read_records,
    write_record,
)

_PUBLISHED = Path("/home/atropichev/.local/bin/agentmarshal")


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, scope: str | None = None
) -> tuple[Path, Path]:
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
    arguments = ["open", "--title", "Research"]
    if scope is not None:
        arguments.extend(["--scope", scope])
    assert main(arguments) == 0
    return repo, repo / ".agentmarshal" / "journal"


def _finding(repo: Path, *, ref: str = "evidence/result.md") -> str:
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
                f"{ref}={digest}",
            ]
        )
        == 0
    )
    records = read_records(repo / ".agentmarshal" / "journal", "CR-001")
    return str(records[-1]["id"])


def _review(finding: str, verdict: str = "approved", *blocking: str) -> None:
    arguments = [
        "submit-review",
        "--task",
        "CR-001",
        "--finding",
        finding,
        "--verdict",
        verdict,
        "--role",
        "reviewer",
        "--vendor",
        "human",
        "--model",
        "none",
        "--email",
        "reviewer@test.invalid",
    ]
    for item in blocking:
        arguments.extend(["--blocking-finding", item])
    assert main(arguments) == 0


def test_finding_lane_passes_and_completion_uses_schema_4_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, journal = _repo(tmp_path, monkeypatch)
    finding = _finding(repo)
    _review(finding)
    capsys.readouterr()

    assert main(["gate", "--task", "CR-001", "--findings"]) == 0
    transcript = capsys.readouterr()
    assert transcript.err == ""
    assert transcript.out.endswith("gate: findings passed\n")
    assert "gate: passed" not in transcript.out
    for label in (
        "scope diff",
        "pipeline attestation",
        "candidate diff",
        "record-path collisions",
        "advisory leak scan",
    ):
        assert f"NOT EXAMINED: {label}" in transcript.out

    assert main(["complete", "--task", "CR-001", "--findings"]) == 0
    completed = read_records(journal, "CR-001")[-1]
    assert completed["schema"] == 4
    assert completed["completed_finding"] == finding
    assert "completed_commit" not in completed


def test_findings_lane_refuses_drift_unresolved_and_nothing_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, journal = _repo(tmp_path, monkeypatch)
    finding = _finding(repo, ref="https://example.invalid/source")
    _review(finding)

    report = run_findings_gate(journal, "CR-001")
    assert not report.passed
    assert any("NOT VERIFIED: artifact https://" in line for line in report.lines)
    assert any("at least one finding artifact" in line for line in report.lines)

    # A newer finding supersedes the all-unresolved one and pins a local copy.
    finding = _finding(repo)
    _review(finding)
    (repo / "evidence" / "result.md").write_text("changed\n", encoding="utf-8")
    report = run_findings_gate(journal, "CR-001")
    assert not report.passed
    assert any(
        "artifact evidence/result.md does not match" in line for line in report.lines
    )


def test_latest_review_must_name_latest_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, journal = _repo(tmp_path, monkeypatch)
    earlier = _finding(repo)
    _review(earlier)
    latest = _finding(repo)

    report = run_findings_gate(journal, "CR-001")

    assert not report.passed
    mismatch = next(line for line in report.lines if "not latest finding" in line)
    assert earlier in mismatch
    assert latest in mismatch


def test_findings_lane_refuses_declared_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, journal = _repo(tmp_path, monkeypatch, scope="src/")
    finding = _finding(repo)
    _review(finding)

    report = run_findings_gate(journal, "CR-001")

    assert not report.passed
    assert any("declared scope: src/" in line for line in report.lines)


def test_acceptance_over_a_finding_names_every_blocking_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, journal = _repo(tmp_path, monkeypatch)
    finding = _finding(repo)
    _review(finding, "changes_required", "F-1", "F-2")
    assert (
        main(
            [
                "accept",
                "--task",
                "CR-001",
                "--finding",
                finding,
                "--by",
                "operator@test.invalid",
                "--reason",
                "accepted risk",
            ]
        )
        == 0
    )

    report = run_findings_gate(journal, "CR-001")

    assert report.passed
    assert any(
        "F-1, F-2" in line and "not an approving review" in line
        for line in report.lines
    )


def test_finding_requires_resolvable_recorder_at_write_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, _ = _repo(tmp_path, monkeypatch)
    monkeypatch.delenv("AGENTMARSHAL_ACTOR")
    _git(repo, "config", "--unset", "user.email")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    artifact = repo / "result.md"
    artifact.write_text("result\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    assert (
        main(
            [
                "finding",
                "--task",
                "CR-001",
                "--summary",
                "x",
                "--artifact",
                f"result.md={digest}",
            ]
        )
        == 1
    )
    assert "requires a resolvable recorder" in capsys.readouterr().err


def test_findings_lane_reads_rewrites_from_journal_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, journal = _repo(tmp_path, monkeypatch)
    finding = _finding(repo)
    _review(finding)
    _git(repo, "add", ".agentmarshal")
    _git(repo, "commit", "--quiet", "-m", "records")
    path = next((journal / "tasks" / "CR-001" / "records").glob("*-finding.json"))
    record = json.loads(path.read_text(encoding="utf-8"))
    record["summary"] = "rewritten"
    path.write_text(json.dumps(record), encoding="utf-8")
    _git(repo, "add", str(path.relative_to(repo)))
    _git(repo, "commit", "--quiet", "-m", "rewrite record")

    report = run_findings_gate(journal, "CR-001")

    assert not report.passed
    assert any(
        "append-only violation" in line and path.name in line for line in report.lines
    )


def test_published_030_accepts_schema_3_and_refuses_schema_4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not _PUBLISHED.is_file():
        pytest.skip(f"published 0.3.0 is absent at {_PUBLISHED}")
    repo, _ = _repo(tmp_path, monkeypatch)
    result = subprocess.run(
        [str(_PUBLISHED), "validate"], cwd=repo, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr

    _finding(repo)
    result = subprocess.run(
        [str(_PUBLISHED), "validate"], cwd=repo, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "unknown or missing schema version" in result.stdout + result.stderr


def test_binding_records_require_exactly_one_target(tmp_path: Path) -> None:
    from agentmarshal.journal.records import create_review_record, write_record

    record = create_review_record(
        "CR-001", "1", "a" * 40, "approved", "r", "v", "m", "r@x", []
    )
    record["schema"] = 4
    record["reviewed_finding"] = "01J00000000000000000000000"
    with pytest.raises(JournalRecordError, match="exactly one"):
        write_record(tmp_path / "journal", "CR-001", record)
    record.pop("reviewed_commit")
    record.pop("reviewed_finding")
    with pytest.raises(JournalRecordError, match="exactly one"):
        write_record(tmp_path / "journal", "CR-001", record)


def test_journal_only_lane_treats_both_completion_bindings_alike(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reports = []
    for binding in ("commit", "finding"):
        root = tmp_path / binding
        root.mkdir()
        repo, journal = _repo(root, monkeypatch)
        _git(repo, "add", ".agentmarshal")
        _git(repo, "commit", "--quiet", "-m", "open")
        base = _git(repo, "rev-parse", "HEAD")
        if binding == "finding":
            finding = _finding(repo)
            record = create_completed_record(
                "CR-001", "1", None, completed_finding=finding
            )
            # Neither a review nor a fresh artifact is re-verified by the
            # journal-only merge lane; it checks transaction shape and history.
            (repo / "evidence" / "result.md").write_text("drifted\n", encoding="utf-8")
        else:
            record = create_completed_record("CR-001", "1", "a" * 40)
        write_record(journal, "CR-001", record)
        _git(repo, "add", ".agentmarshal")
        _git(repo, "commit", "--quiet", "-m", "complete")
        head = _git(repo, "rev-parse", "HEAD")
        reports.append(run_gate(repo, "CR-001", head, base, head))

    assert reports[0].passed and reports[1].passed
    assert reports[0].lines[:2] == reports[1].lines[:2]
    assert all(
        report.lines[2].startswith("PASS: pipeline attested for ") for report in reports
    )
    assert reports[0].lines[3:] == reports[1].lines[3:]


def test_findings_lane_refuses_reviewer_who_is_the_recorder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Independence compares git identities, not labels (ADR-0009 Decision 3).

    The recorder is the ``researcher`` override, mapped by the actors table to
    ``recorder@test.invalid``. A review signed with that very email is the
    recorder reviewing themself and must be refused. A comparison that used the
    override string instead of the mapped identity would let it pass — which is
    what this test exists to notice.
    """

    repo, _ = _repo(tmp_path, monkeypatch)
    finding = _finding(repo)
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--finding",
                finding,
                "--verdict",
                "approved",
                "--role",
                "reviewer",
                "--vendor",
                "human",
                "--model",
                "none",
                "--email",
                "recorder@test.invalid",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert main(["gate", "--task", "CR-001", "--findings"]) == 1
    transcript = capsys.readouterr()
    assert "FAIL:" in transcript.out
    assert "declared reviewer identity" in transcript.out
    assert "gate: findings passed" not in transcript.out
