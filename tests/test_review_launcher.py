"""Tests for the read-only review launcher."""

import json
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import review
from agentmarshal.journal.records import read_records


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _review_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "--allow-empty",
        "--quiet",
        "-m",
        "init",
    )
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Review task"]) == 0
    _git(repo, "add", ".agentmarshal")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "--quiet",
        "-m",
        "open review task",
    )
    return repo, _git(repo, "rev-parse", "HEAD")


def _reviewer_stub(
    tmp_path: Path,
    output: str,
    exit_code: int = 0,
    prompt_output: Path | None = None,
) -> Path:
    stub = tmp_path / "reviewer.py"
    capture_prompt = (
        ""
        if prompt_output is None
        else "from pathlib import Path\n"
        f"Path({str(prompt_output)!r}).write_text(sys.stdin.read(), encoding='utf-8')\n"
    )
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"{capture_prompt}"
        f"sys.stdout.write({output!r})\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return stub


def _review_args(commit: str) -> list[str]:
    return [
        "review",
        "--task",
        "CR-001",
        "--commit",
        commit,
        "--base",
        "HEAD",
        "--role",
        "reviewer",
        "--vendor",
        "test",
        "--model",
        "test-model",
        "--email",
        "reviewer@example.invalid",
    ]


def _verdict(
    commit: str,
    verdict: str,
    findings: list[str],
    advisory_findings: list[str] | None = None,
) -> str:
    data: dict[str, object] = {
        "reviewed_commit": commit,
        "verdict": verdict,
        "findings": findings,
    }
    if advisory_findings is not None:
        data["advisory_findings"] = advisory_findings
    return f"AGENTMARSHAL_VERDICT_BEGIN\n{json.dumps(data)}\nAGENTMARSHAL_VERDICT_END\n"


def _kept_outputs() -> list[Path]:
    import tempfile as _tempfile

    return list(
        Path(_tempfile.gettempdir()).glob("agentmarshal-rejected-verdict-*.txt")
    )


def _assert_no_snapshot(repo: Path) -> None:
    import tempfile as _tempfile

    leftovers = list(Path(_tempfile.gettempdir()).glob("agentmarshal-review-*"))
    assert leftovers == []
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def _metadata_probe_reviewer_stub(tmp_path: Path, output: str) -> Path:
    """Stub failing if the snapshot exposes git metadata; writes into the
    snapshot to prove writes stay in the ephemeral copy."""

    stub = tmp_path / "probing-reviewer.py"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import sys\n"
        "if Path('.git').exists():\n"
        "    raise SystemExit('snapshot exposes git metadata')\n"
        "Path('reviewer-scratch.txt').write_text('ephemeral', encoding='utf-8')\n"
        f"sys.stdout.write({output!r})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return stub


def test_snapshot_has_no_git_metadata_and_writes_stay_ephemeral(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _metadata_probe_reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert main(_review_args(commit)) == 0

    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 2
    assert not (repo / "reviewer-scratch.txt").exists()
    _assert_no_snapshot(repo)


def test_review_of_commit_without_contract_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _commit = _review_repo(tmp_path, monkeypatch)
    first_commit = _git(repo, "rev-list", "--max-parents=0", "HEAD")
    stub = _reviewer_stub(tmp_path, _verdict(first_commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    # The root commit has an empty tree: no contract, and its archive is
    # a lone pax_global_header — both must fail closed, not crash.
    assert main(_review_args(first_commit)) == 1

    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)


def test_snapshot_extraction_failure_leaves_no_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    def failing_extract(project_root: Path, sha: str, snapshot: Path) -> None:
        raise review.ReviewLaunchError("git archive failed: simulated")

    monkeypatch.setattr(review, "_extract_snapshot", failing_extract)

    assert main(_review_args(commit)) == 1

    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)


def test_reviewer_command_requires_explicit_command_no_bundled_vendor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompt_file = tmp_path / "review-prompt.txt"

    # Model-agnostic: no reviewer is bundled, so an unset command fails closed.
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)
    with pytest.raises(review.ReviewLaunchError, match="AGENTMARSHAL_REVIEWER_CMD"):
        review._reviewer_command("test-model", prompt_file)

    # With a command set, {model} is substituted and the prompt goes on stdin.
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD",
        "codex exec --sandbox read-only --model {model} -",
    )
    assert review._reviewer_command("test-model", prompt_file) == [
        "codex",
        "exec",
        "--sandbox",
        "read-only",
        "--model",
        "test-model",
        "-",
    ]


def test_review_uses_contract_from_reviewed_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    prompt_output = tmp_path / "review-prompt.txt"
    stub = _reviewer_stub(
        tmp_path,
        _verdict(commit, "approved", []),
        prompt_output=prompt_output,
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    contract_path = (
        repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    )
    contract_path.write_text(
        f"{contract_path.read_text(encoding='utf-8')}\nUNCOMMITTED CONTRACT CHANGE\n",
        encoding="utf-8",
    )

    assert main(_review_args(commit)) == 0

    prompt = prompt_output.read_text(encoding="utf-8")
    assert "Review task" in prompt
    assert "UNCOMMITTED CONTRACT CHANGE" not in prompt
    _assert_no_snapshot(repo)


@pytest.mark.parametrize(
    ("verdict", "findings"),
    [("approved", []), ("changes_required", ["F-001"])],
)
def test_review_records_stub_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    verdict: str,
    findings: list[str],
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(commit, verdict, findings))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(_review_args(commit)) == 0

    records = read_records(repo / ".agentmarshal" / "journal", "CR-001")
    assert records[-1]["reviewed_commit"] == commit
    assert records[-1]["verdict"] == verdict
    assert records[-1]["findings"] == findings
    capsys.readouterr()
    assert main(["status", "CR-001"]) == 0
    assert "reviewed_commit=" in main_output(capsys)
    _assert_no_snapshot(repo)


def main_output(capsys: pytest.CaptureFixture[str]) -> str:
    return capsys.readouterr().out


@pytest.mark.parametrize(
    "case",
    [
        "adapter_failure",
        "missing_sentinels",
        "invalid_json",
        "commit_mismatch",
        "rejected_verdict",
    ],
)
def test_review_failure_leaves_no_record_or_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    output = {
        "adapter_failure": "",
        "missing_sentinels": "not a verdict\n",
        "invalid_json": "AGENTMARSHAL_VERDICT_BEGIN\nnope\nAGENTMARSHAL_VERDICT_END\n",
        "commit_mismatch": _verdict("0" * 40, "approved", []),
        "rejected_verdict": _verdict(commit, "approved", ["F-001"]),
    }[case]
    exit_code = 1 if case == "adapter_failure" else 0
    stub = _reviewer_stub(tmp_path, output, exit_code)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(_review_args(commit)) == 1

    assert read_records(repo / ".agentmarshal" / "journal", "CR-001")
    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)


@pytest.mark.parametrize(
    ("task", "commit"),
    [("CR-999", "HEAD"), ("CR-001", "not-a-commit")],
)
def test_review_rejects_unknown_task_or_commit_before_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    task: str,
    commit: str,
) -> None:
    repo, head = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(tmp_path, _verdict(head, "approved", []))
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    arguments = _review_args(commit)
    arguments[arguments.index("CR-001")] = task

    assert main(arguments) == 1

    assert len(read_records(repo / ".agentmarshal" / "journal", "CR-001")) == 1
    _assert_no_snapshot(repo)


def test_prompt_lists_the_allowed_verdicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The prompt must name the verdicts, from the definition validation uses."""

    from agentmarshal.journal.records import _REVIEW_VERDICTS
    from agentmarshal.journal.review import _review_prompt

    prompt = _review_prompt("contract", "diff", "a" * 40)

    for verdict in _REVIEW_VERDICTS:
        assert verdict in prompt
    assert "advisory_findings" in prompt


def test_advisory_findings_reach_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """advisory_findings is in the schema; the protocol must be able to produce it."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path, _verdict(commit, "approved", [], advisory_findings=["A-001"])
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert (
        main(
            [
                "review",
                "--task",
                "CR-001",
                "--commit",
                commit,
                "--base",
                "HEAD~1",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                "reviewer@test.invalid",
            ]
        )
        == 0
    )

    records = read_records(repo / ".agentmarshal" / "journal", "CR-001")
    assert records[-1]["advisory_findings"] == ["A-001"]


def test_rejected_verdict_keeps_the_reviewer_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A rejected verdict must not discard the analysis that was paid for."""

    before = set(_kept_outputs())
    _repo, commit = _review_repo(tmp_path, monkeypatch)
    analysis = "the reviewer's reasoning that must survive"
    stub = _reviewer_stub(
        tmp_path,
        f'{analysis}\nAGENTMARSHAL_VERDICT_BEGIN\n{{"verdict": "approved"}}\n'
        "AGENTMARSHAL_VERDICT_END\n",
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert (
        main(
            [
                "review",
                "--task",
                "CR-001",
                "--commit",
                commit,
                "--base",
                "HEAD~1",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                "reviewer@test.invalid",
            ]
        )
        == 1
    )

    message = capsys.readouterr().err
    assert "missing required field(s)" in message
    assert "reviewed_commit" in message and "findings" in message
    kept = [path for path in _kept_outputs() if path not in before]
    try:
        assert len(kept) == 1, message
        assert str(kept[0]) in message
        assert analysis in kept[0].read_text(encoding="utf-8")
    finally:
        for path in kept:
            path.unlink(missing_ok=True)


def test_unsupported_verdict_key_is_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown key still fails closed, but the operator is told which one."""

    before = set(_kept_outputs())
    _repo, commit = _review_repo(tmp_path, monkeypatch)
    payload = json.dumps(
        {
            "reviewed_commit": commit,
            "verdict": "approved",
            "findings": [],
            "confidence": 0.9,
        }
    )
    stub = _reviewer_stub(
        tmp_path,
        f"AGENTMARSHAL_VERDICT_BEGIN\n{payload}\nAGENTMARSHAL_VERDICT_END\n",
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert (
        main(
            [
                "review",
                "--task",
                "CR-001",
                "--commit",
                commit,
                "--base",
                "HEAD~1",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                "reviewer@test.invalid",
            ]
        )
        == 1
    )

    message = capsys.readouterr().err
    assert "unsupported field(s): confidence" in message
    for path in _kept_outputs():
        if path not in before:
            path.unlink(missing_ok=True)
