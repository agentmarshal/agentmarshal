"""Tests for the onboarding health check command."""

import json
import subprocess
from pathlib import Path

import pytest

import agentmarshal.doctor as doctor
from agentmarshal.cli import main
from agentmarshal.doctor import run_doctor


def write_project_file(repo: Path, content: str) -> None:
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text(content, encoding="utf-8")


def init_git_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    # Give the repository an identity of its own. Without one these tests read
    # whatever the machine has configured: locally a developer's, on a runner
    # none at all, and the actor check reports a different case in each.
    for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
        subprocess.run(["git", "config", key, value], cwd=repo, check=True)


@pytest.fixture(autouse=True)
def clear_precondition_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep doctor checks independent of the test runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)


def write_validate_workflow(repo: Path) -> None:
    workflow = repo / ".github" / "workflows" / "governance.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "jobs:\n  validate:\n    run: agentmarshal validate\n", encoding="utf-8"
    )


def test_doctor_reports_every_precondition_met(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a project with every precondition met reports so."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 1}\n')
    write_validate_workflow(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "implementation-agent")
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", "reviewer --model {model} {prompt_file}"
    )

    assert main(["doctor"]) == 0

    output = capsys.readouterr().out
    assert output.count("OK:") == 10
    assert "Summary: all 10 checks passed" in output


def test_doctor_reports_unset_actor_variable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unset actor variable is reported."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 1}\n')
    write_validate_workflow(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", "reviewer --model {model} {prompt_file}"
    )

    assert main(["doctor"]) == 0

    output = capsys.readouterr().out
    assert "TODO: recorded actor" in output
    assert "the invoking git identity" in output
    assert "indistinguishable from that person" in output
    assert "Summary: 1 precondition(s) left to the operator" in output


def test_doctor_does_not_report_an_unset_reviewer_command_as_a_fault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A journal reviewed by hand has no reviewer command, and that is a
    configuration the quickstart offers, not something to repair."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 1}\n')
    write_validate_workflow(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "implementation-agent")
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)

    results = {result.name: result for result in run_doctor(repo)}

    assert results["reviewer command placeholders"].ok
    assert "submit-review" in results["reviewer command placeholders"].detail


def test_doctor_reports_unresolvable_reviewer_command_without_its_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a reviewer command with an unresolvable placeholder is reported."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 1}\n')
    write_validate_workflow(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "implementation-agent")
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", "reviewer --key s3cret {unsupported}"
    )

    assert main(["doctor"]) == 0

    output = capsys.readouterr().out
    assert "TODO: reviewer command placeholders" in output
    assert "a review cannot launch" in output
    assert "s3cret" not in output


def test_doctor_reports_whether_a_ci_definition_invokes_validate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The local CI check distinguishes a missing workflow from a valid one."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 1}\n')
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "implementation-agent")
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", "reviewer --model {model} {prompt_file}"
    )

    without_ci = {result.name: result for result in run_doctor()}
    assert not without_ci["CI validate definition"].ok
    assert (
        "journal integrity is not checked before merge"
        in without_ci["CI validate definition"].detail
    )

    write_validate_workflow(repo)
    with_ci = {result.name: result for result in run_doctor()}
    assert with_ci["CI validate definition"].ok


def test_doctor_reports_outside_git_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    assert main(["doctor"]) == 1

    output = capsys.readouterr().out
    assert "FAIL: git repository" in output
    assert "FAIL: project initialized" in output


def test_doctor_reports_missing_project_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    monkeypatch.chdir(repo)

    assert main(["doctor"]) == 1

    assert "FAIL: project initialized" in capsys.readouterr().out


def test_doctor_reports_unknown_project_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 2}\n')
    monkeypatch.chdir(repo)

    assert main(["doctor"]) == 1

    assert "FAIL: project schema" in capsys.readouterr().out


def test_doctor_reports_malformed_project_file_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, "not json\n")
    monkeypatch.chdir(repo)

    assert main(["doctor"]) == 1

    output = capsys.readouterr()
    assert "FAIL: project schema" in output.out
    assert "Traceback" not in output.err


def test_doctor_reports_missing_git_executable(tmp_path: Path) -> None:
    results = run_doctor(tmp_path, resolver=lambda _name: None)

    git_result = results[0]
    assert not git_result.ok
    assert git_result.name == "git"


def test_doctor_handles_git_discovery_decode_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 1}\n')
    monkeypatch.chdir(repo)

    def raise_decode_error(_start: Path) -> Path | None:
        raise UnicodeDecodeError("utf-8", b"\\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(doctor, "find_git_root", raise_decode_error)

    assert main(["doctor"]) == 1

    output = capsys.readouterr()
    assert output.out.count("FAIL:") == 6
    assert output.out.count("TODO:") == 2
    assert "FAIL: git repository — cannot determine git repository" in output.out
    assert "FAIL: project schema — cannot determine project location" in output.out
    assert (
        "FAIL: project setting review.finding_classes — "
        "cannot determine project location" in output.out
    )
    assert (
        "Summary: 6 check(s) failed, 2 precondition(s) left to the operator"
        in output.out
    )
    assert "Traceback" not in output.err


def test_doctor_reports_a_malformed_setting_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed key fails its own check."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(
        repo, '{"schema": 1, "review": {"changes_required_threshold": true}}\n'
    )
    monkeypatch.chdir(repo)

    assert main(["doctor"]) == 1

    output = capsys.readouterr().out
    assert (
        "FAIL: project setting review.changes_required_threshold — "
        "project.json key 'review.changes_required_threshold' must be "
        "an integer of at least 1" in output
    )
    assert "OK: project setting review.finding_classes" in output
    assert "OK: project setting contract.require_agreement" in output


def test_doctor_reports_each_malformed_setting_key(tmp_path: Path) -> None:
    """Scenario: several malformed keys each fail their own check."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(
        repo,
        '{"schema": 1, "review": {"finding_classes": []},'
        ' "contract": {"require_agreement": "yes"}}\n',
    )

    results = {result.name: result for result in run_doctor(repo)}

    classes = results["project setting review.finding_classes"]
    assert not classes.ok
    assert "review.finding_classes" in classes.detail
    assert "non-empty list of distinct non-empty strings" in classes.detail
    agreement = results["project setting contract.require_agreement"]
    assert not agreement.ok
    assert "contract.require_agreement" in agreement.detail
    assert "a boolean" in agreement.detail
    assert results["project setting review.changes_required_threshold"].ok


def test_doctor_passes_settings_for_a_project_with_none_of_the_keys(
    tmp_path: Path,
) -> None:
    """Scenario: a project with none of the keys passes."""

    repo = tmp_path / "repo"
    init_git_repo(repo)
    write_project_file(repo, '{"schema": 1}\n')

    results = {result.name: result for result in run_doctor(repo)}

    for key in (
        "review.finding_classes",
        "review.changes_required_threshold",
        "contract.require_agreement",
    ):
        assert results[f"project setting {key}"].ok


def test_doctor_in_a_sidecar_reads_the_journal_repositorys_settings(
    tmp_path: Path,
) -> None:
    """Scenario: a sidecar reads the journal repository's settings."""

    host = tmp_path / "host"
    journal_repo = tmp_path / "journal"
    init_git_repo(host)
    init_git_repo(journal_repo)
    write_project_file(
        journal_repo,
        json.dumps(
            {
                "schema": 1,
                "placement": "sidecar",
                "host": str(host),
                "contract": {"require_agreement": "yes"},
            }
        )
        + "\n",
    )

    results = {result.name: result for result in run_doctor(journal_repo)}

    agreement = results["project setting contract.require_agreement"]
    assert not agreement.ok
    assert "contract.require_agreement" in agreement.detail
    assert "a boolean" in agreement.detail
