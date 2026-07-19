"""Tests for the merge gate."""

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.gate import GateError, run_gate

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
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--verdict",
                "changes_required",
                "--finding",
                "F-001",
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

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "review" in output


def test_gate_refuses_dependent_reviewer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head, email="worker@test.invalid")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "independent" in output


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
