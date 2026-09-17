"""CLI tests."""

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main


def init_git_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)


def test_init_names_preconditions_it_cannot_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a fresh project is told what remains."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    monkeypatch.chdir(repo)

    assert main(["init"]) == 0

    output = capsys.readouterr().out
    assert output.count("Before the first governed task") == 1
    assert "disable squash and rebase merges" in output
    assert "rewrites the reviewed SHA" in output
    assert "AGENTMARSHAL_ACTOR" in output
    assert "resolve to the invoking git identity" in output


def test_doctor_preconditions_are_report_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unmet preconditions advise without turning doctor into a gate."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    (repo / ".agentmarshal").mkdir()
    (repo / ".agentmarshal" / "project.json").write_text(
        '{"schema": 1}\n', encoding="utf-8"
    )
    monkeypatch.chdir(repo)
    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)

    assert main(["doctor"]) == 0

    output = capsys.readouterr().out
    assert "Summary: 2 check(s) reported unmet" in output
    assert "all" not in output.splitlines()[-1]


def test_review_dry_run_help_says_it_records_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Task 3.4: the dry-run flag says that it records nothing."""

    with pytest.raises(SystemExit) as raised:
        main(["review", "--help"])

    assert raised.value.code == 0
    assert "records nothing" in capsys.readouterr().out
