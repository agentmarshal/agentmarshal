"""Tests for the read-only review launcher."""

import hashlib
import importlib
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import review
from agentmarshal.journal.records import (
    create_review_record,
    read_records,
    write_record,
)


@pytest.fixture(autouse=True)
def _isolated_temp_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    system_temp = Path(tempfile.gettempdir())
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)
    return system_temp


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


def _kept_outputs(tmp_path: Path) -> list[Path]:
    return list(tmp_path.glob("agentmarshal-rejected-verdict-*.txt"))


def _kept_any_outputs(tmp_path: Path) -> list[Path]:
    """Every file the launcher could have left in the temp dir, any prefix."""

    return list(tmp_path.glob("agentmarshal-*.txt"))


def _run_review(commit: str) -> int:
    return main(
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


def _assert_no_snapshot(repo: Path, tmp_path: Path) -> None:
    leftovers = list(tmp_path.glob("agentmarshal-review-*"))
    assert leftovers == []
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1


def test_snapshot_assertion_is_isolated_and_still_detects_leaks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    _isolated_temp_directory: Path,
) -> None:
    repo, commit = _review_repo(tmp_path, monkeypatch)
    unrelated = Path(
        tempfile.mkdtemp(
            prefix="agentmarshal-review-unrelated-",
            dir=_isolated_temp_directory,
        )
    )
    try:
        _assert_no_snapshot(repo, tmp_path)

        class LeakingTemporaryDirectory:
            def __init__(self, *, prefix: str) -> None:
                self.path = tempfile.mkdtemp(prefix=prefix)

            def __enter__(self) -> str:
                return self.path

            def __exit__(self, *args: object) -> None:
                return None

        stub = _reviewer_stub(tmp_path, _verdict(commit, "approved", []))
        monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
        monkeypatch.setattr(tempfile, "TemporaryDirectory", LeakingTemporaryDirectory)
        assert main(_review_args(commit)) == 0

        with pytest.raises(AssertionError):
            _assert_no_snapshot(repo, tmp_path)
    finally:
        unrelated.rmdir()


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
    _assert_no_snapshot(repo, tmp_path)


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
    _assert_no_snapshot(repo, tmp_path)


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
    _assert_no_snapshot(repo, tmp_path)


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
    _assert_no_snapshot(repo, tmp_path)


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
    _assert_no_snapshot(repo, tmp_path)


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
    _assert_no_snapshot(repo, tmp_path)


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
    _assert_no_snapshot(repo, tmp_path)


def test_prompt_requests_human_readable_claims_and_lists_the_allowed_verdicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Finding labels need prose, while verdicts come from record validation."""

    from agentmarshal.journal.records import _REVIEW_VERDICTS
    from agentmarshal.journal.review import _review_prompt

    prompt = _review_prompt("contract", "diff", "a" * 40)

    prose_request = "For each blocking or advisory finding id you report"
    assert prose_request in prompt
    assert "print one line of prose" in prompt
    assert "before the verdict block, naming what is wrong and where" in prompt
    assert "ids are labels\nfor the machine" in prompt
    assert "the prose is what a human will read" in prompt
    assert prompt.index(prose_request) < prompt.index("At the end, print exactly")
    for verdict in _REVIEW_VERDICTS:
        assert verdict in prompt
    assert "advisory_findings" in prompt


def test_prompt_lists_named_decisions_and_documents() -> None:
    prompt = review._review_prompt(
        "contract",
        "diff",
        "a" * 40,
        decisions=("ADR-0010",),
        documents=("docs/guide.md", "openspec/specs/"),
    )

    assert "Decisions:\n- ADR-0010" in prompt
    assert "Documents:\n- docs/guide.md\n- openspec/specs/" in prompt
    assert "A finding may cite a contradiction with a named decision." in prompt


def test_review_prompt_resolves_extension_documents_from_reviewed_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _ = _review_repo(tmp_path, monkeypatch)
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(
            "schema = 1\n",
            "schema = 2\ndecisions = ['ADR-0010']\n"
            "documents = ['docs/guide.md']\n"
            "extensions = ['openspec']\n",
        ),
        encoding="utf-8",
    )
    manifest = repo / ".agentmarshal" / "extensions" / "openspec.toml"
    manifest.parent.mkdir()
    manifest.write_text(
        "schema = 1\n"
        'name = "openspec"\n'
        'version = "1"\n'
        'footprint = ["openspec/"]\n'
        'documents = ["openspec/specs/"]\n'
        "artifacts = []\n"
        'install = "install"\n'
        'remove = "remove"\n',
        encoding="utf-8",
    )
    _git(repo, "add", str(contract.relative_to(repo)), str(manifest.relative_to(repo)))
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "--quiet",
        "-m",
        "name review material",
    )
    commit = _git(repo, "rev-parse", "HEAD")
    prompt_output = tmp_path / "review-prompt.txt"
    stub = _reviewer_stub(
        tmp_path,
        _verdict(commit, "approved", []),
        prompt_output=prompt_output,
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert main(_review_args(commit)) == 0

    prompt = prompt_output.read_text(encoding="utf-8")
    assert "Decisions:\n- ADR-0010" in prompt
    assert "Documents:\n- docs/guide.md\n- openspec/specs/" in prompt


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


def test_model_review_path_keeps_its_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the model review path keeps its output."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    output = "verbatim reviewer prose\n" + _verdict(commit, "approved", [])
    stub = _reviewer_stub(tmp_path, output)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    journal = repo / ".agentmarshal" / "journal"
    record = read_records(journal, "CR-001")[-1]
    artifacts = record["artifacts"]
    assert isinstance(artifacts, list)
    artifact = artifacts[0]
    assert isinstance(artifact, dict)
    expected_ref = (
        f".agentmarshal/journal/tasks/CR-001/artifacts/{record['id']}-review.md"
    )
    assert artifact == {
        "ref": expected_ref,
        "hash": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }
    assert (repo / expected_ref).read_bytes() == output.encode("utf-8")


def test_rejected_verdict_keeps_the_reviewer_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A rejected verdict must not discard the analysis that was paid for."""

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
    kept = _kept_outputs(tmp_path)
    try:
        assert len(kept) == 1, message
        assert str(kept[0]) in message
        assert analysis in kept[0].read_text(encoding="utf-8")
    finally:
        for path in kept:
            path.unlink(missing_ok=True)


def test_rejected_verdict_still_keeps_the_prose(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a rejected verdict still keeps the prose."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    output = "prose from a rejected verdict\nAGENTMARSHAL_VERDICT_BEGIN\n{}\n"
    output += "AGENTMARSHAL_VERDICT_END\n"
    stub = _reviewer_stub(tmp_path, output)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 1

    message = capsys.readouterr().err
    kept = _kept_outputs(tmp_path)
    try:
        assert len(kept) == 1
        assert str(kept[0]) in message
        assert kept[0].read_text(encoding="utf-8") == output
        records = read_records(repo / ".agentmarshal" / "journal", "CR-001")
        assert [record["record_type"] for record in records] == ["opened"]
    finally:
        for path in kept:
            path.unlink(missing_ok=True)


def test_unsupported_verdict_key_is_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown key still fails closed, but the operator is told which one."""

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
    for path in _kept_outputs(tmp_path):
        path.unlink(missing_ok=True)


def test_record_validation_failure_also_keeps_the_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A verdict can parse and still be refused by record validation.

    That path — an approving verdict carrying findings — is the one seen most
    often in practice, and it discarded the analysis as surely as a parse error.
    """

    _repo, commit = _review_repo(tmp_path, monkeypatch)
    analysis = "reasoning that must survive a record-validation refusal"
    stub = _reviewer_stub(
        tmp_path, analysis + "\n" + _verdict(commit, "approved", ["F-001"])
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
    kept = _kept_outputs(tmp_path)
    try:
        assert len(kept) == 1, message
        assert str(kept[0]) in message
        assert analysis in kept[0].read_text(encoding="utf-8")
    finally:
        for path in kept:
            path.unlink(missing_ok=True)


@pytest.mark.parametrize(
    ("verdict", "findings", "advisory"),
    [
        ("changes_required", ["F-001"], None),
        ("approved", [], ["F-002"]),
    ],
)
def test_an_accepted_verdict_keeps_no_copy_outside_the_journal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    verdict: str,
    findings: list[str],
    advisory: list[str] | None,
) -> None:
    """Scenario: an accepted verdict keeps no copy outside the journal."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    analysis = "reasoning kept only as pinned journal evidence"
    stub = _reviewer_stub(
        tmp_path,
        analysis + "\n" + _verdict(commit, verdict, findings, advisory),
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert _run_review(commit) == 0

    captured = capsys.readouterr()
    assert _kept_any_outputs(tmp_path) == []
    assert "reviewer prose pinned: .agentmarshal/journal/tasks/CR-001/artifacts/" in (
        captured.err
    )
    assert "kept at" not in captured.err
    assert captured.out.strip().endswith(".json")
    assert len(captured.out.strip().splitlines()) == 1
    artifact = next((repo / ".agentmarshal/journal/tasks/CR-001/artifacts").iterdir())
    assert analysis in artifact.read_text(encoding="utf-8")


def test_a_clean_approval_keeps_nothing_and_says_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With no finding there is no claim to explain, and no file to leave behind."""

    _repo, commit = _review_repo(tmp_path, monkeypatch)
    stub = _reviewer_stub(
        tmp_path, "nothing to report\n" + _verdict(commit, "approved", [])
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    captured = capsys.readouterr()
    kept = _kept_any_outputs(tmp_path)
    try:
        assert kept == []
        assert "kept at" not in captured.err
    finally:
        for path in kept:
            path.unlink(missing_ok=True)


def test_a_failure_after_the_pin_names_the_artifact_and_keeps_no_other_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a refusal the writer cannot foresee is named as a limit — on
    the model path too: the artifact is named, and no temporary copy joins it."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    root = repo / ".agentmarshal" / "journal"
    record_id = "01J00000000000000000000000"
    earlier = create_review_record(
        "CR-001",
        "test",
        commit,
        "approved",
        "reviewer",
        "human",
        "none",
        "reviewer@test.invalid",
        [],
    )
    write_record(root, "CR-001", earlier, record_id=record_id)
    submit_review_module = importlib.import_module("agentmarshal.journal.submit_review")
    monkeypatch.setattr(submit_review_module, "generate_ulid", lambda: record_id)
    stub = _reviewer_stub(
        tmp_path, "reasoning\n" + _verdict(commit, "changes_required", ["F-001"])
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert _run_review(commit) == 1

    captured = capsys.readouterr()
    kept = _kept_any_outputs(tmp_path)
    try:
        assert kept == [], captured.err
        artifact_ref = (
            f".agentmarshal/journal/tasks/CR-001/artifacts/{record_id}-review.md"
        )
        assert f"reviewer prose artifact left at {artifact_ref}" in captured.err
        assert "kept at" not in captured.err
        assert (repo / artifact_ref).read_bytes().startswith(b"reasoning\n")
    finally:
        for path in kept:
            path.unlink(missing_ok=True)


def test_prompt_without_named_material_is_the_prompt_written_before_schema_2() -> None:
    """The 0.3.0 prompt, pinned literally: the split into a prefix and a suffix
    must reproduce it, and this is the test that would notice a seam."""

    from agentmarshal.journal.records import _REVIEW_VERDICTS
    from agentmarshal.journal.review import _VERDICT_BEGIN, _VERDICT_END

    verdicts = ", ".join(sorted(_REVIEW_VERDICTS))
    commit = "b" * 40
    expected = f"""You are a read-only code reviewer. Review the supplied task contract
and diff.
Do not modify files. Your reviewed commit is {commit}.

For each blocking or advisory finding id you report, print one line of prose
before the verdict block, naming what is wrong and where. The ids are labels
for the machine; the prose is what a human will read.

At the end, print exactly one JSON object between lines containing exactly
{_VERDICT_BEGIN} and {_VERDICT_END}. The object must contain:
- reviewed_commit: the exact reviewed commit SHA
- verdict: exactly one of: {verdicts}
- findings: an array of unique finding-id strings; empty only for "approved",
  and non-empty for every other verdict
and may additionally contain:
- advisory_findings: an array of unique non-blocking finding-id strings,
  disjoint from findings; allowed with any verdict, including "approved"

No other key is accepted.

Task contract:
CONTRACT

Diff:
DIFF
"""

    assert review._review_prompt("CONTRACT", "DIFF", commit) == expected


def test_review_launches_when_a_named_manifest_is_absent_from_the_reviewed_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A removal candidate deletes its manifest; the review must still launch."""

    repo, _ = _review_repo(tmp_path, monkeypatch)
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(
            "schema = 1\n", "schema = 2\nextensions = ['openspec']\n"
        ),
        encoding="utf-8",
    )
    _git(repo, "add", str(contract.relative_to(repo)))
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "--quiet",
        "-m",
        "name an extension whose manifest is gone",
    )
    commit = _git(repo, "rev-parse", "HEAD")
    prompt_output = tmp_path / "review-prompt.txt"
    stub = _reviewer_stub(
        tmp_path,
        _verdict(commit, "approved", []),
        prompt_output=prompt_output,
    )
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert main(_review_args(commit)) == 0

    prompt = prompt_output.read_text(encoding="utf-8")
    assert (
        "Extensions whose manifest is absent in the reviewed tree:\n- openspec"
        in prompt
    )


def test_pinned_prose_is_announced(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The operator is told where the pinned prose is."""

    _repo, commit = _review_repo(tmp_path, monkeypatch)
    output = "one finding, explained\n" + _verdict(commit, "approved", [], ["A-1"])
    stub = _reviewer_stub(tmp_path, output)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert _run_review(commit) == 0

    captured = capsys.readouterr()
    assert "reviewer prose pinned: .agentmarshal/journal/tasks/CR-001/artifacts/" in (
        captured.err
    )


def test_pinned_prose_keeps_the_reviewer_bytes_including_crlf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the model review path keeps its output — as received, not
    newline-normalised."""

    repo, commit = _review_repo(tmp_path, monkeypatch)
    output = "first line\r\nsecond line\r\n" + _verdict(commit, "approved", [])
    stub = _reviewer_stub(tmp_path, output)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))

    assert _run_review(commit) == 0

    artifacts = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts"
    artifact = next(artifacts.iterdir())
    assert artifact.read_bytes().startswith(b"first line\r\nsecond line\r\n")
