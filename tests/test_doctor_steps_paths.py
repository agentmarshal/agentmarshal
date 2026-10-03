"""Tests for ``doctor`` reporting overdue steps, the paths and the git floor.

ADR-0014 decision 9 — as amended 2026-10-03 — and decision 13: ``doctor``
shows the steps past their deadline and prints where the journal, the
process log and the local state live; local state resolves through
``git rev-parse --path-format=absolute``, which needs git 2.31.
"""

from __future__ import annotations

import io
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

import agentmarshal.doctor as doctor
from agentmarshal import steps
from agentmarshal.cli import main
from agentmarshal.doctor import run_doctor
from agentmarshal.journal.display import escape_for_display
from agentmarshal.journal.placement import Placement
from agentmarshal.journal.records import create_opened_record, write_record
from agentmarshal.localstate import LocalState, LocalStateError
from agentmarshal.process_log import open_writer, read_events, write_event

_CONTRACT = (
    "+++\nschema = 1\nid = '{id}'\ntitle = 'Task'\nscope = []\n"
    "acceptance = []\n+++\n\n# {id}\n"
)


@pytest.fixture(autouse=True)
def clear_precondition_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep doctor checks independent of the test runner's environment."""

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)
    monkeypatch.delenv("AGENTMARSHAL_REVIEWER_CMD", raising=False)


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    # Give the repository an identity of its own, the way test_doctor.py's
    # fixture does: without one the actor check reads whatever the machine
    # has configured.
    for key, value in (("user.name", "Test"), ("user.email", "test@example.invalid")):
        subprocess.run(["git", "config", key, value], cwd=repo, check=True)


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    _init_repo(repo)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def _every_precondition_met(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workflow = repo / ".github" / "workflows" / "governance.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "jobs:\n  validate:\n    run: agentmarshal validate\n", encoding="utf-8"
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "implementation-agent")
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", "reviewer --model {model} {prompt_file}"
    )


def _task(repo: Path, task_id: str) -> None:
    journal = repo / ".agentmarshal" / "journal"
    task_directory = journal / "tasks" / task_id
    task_directory.mkdir(parents=True)
    (task_directory / "contract.md").write_text(
        _CONTRACT.format(id=task_id), encoding="utf-8"
    )
    write_record(journal, task_id, create_opened_record(task_id, "1.0"))


def _state(repo: Path) -> LocalState:
    return LocalState((repo / ".git").resolve() / "agentmarshal")


def _log_step(
    repo: Path,
    step: str,
    *,
    activity: str = "implementation",
    deadline: str = "2026-01-01T00:00:00+00:00",
    task: str = "CR-001",
) -> None:
    writer = open_writer(_state(repo))
    write_event(
        writer,
        "step-started",
        task=task,
        step=step,
        activity=activity,
        pid=1,
        pid_started_at="unknown",
        deadline=deadline,
    )


def _paths_lines(repo: Path) -> str:
    state = _state(repo)
    return (
        f"journal: {repo.resolve() / '.agentmarshal' / 'journal'}\n"
        f"process log: {state.log}\n"
        f"local state: {state.root}\n"
    )


def test_doctor_lists_every_overdue_step_across_the_projects_tasks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: doctor lists every overdue step across the project's
    tasks."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _task(repo, "CR-002")
    _task(repo, "CR-003")
    _log_step(repo, "S1", task="CR-001", deadline="2026-01-01T00:00:00+00:00")
    _log_step(
        repo,
        "S2",
        task="CR-002",
        activity="review",
        deadline="2026-01-02T00:00:00+00:00",
    )

    main(["doctor"])

    err = capsys.readouterr().err
    assert (
        "Overdue step (this machine's process log): task=CR-001 step=S1 "
        "activity=implementation deadline=2026-01-01T00:00:00+00:00 past="
    ) in err
    assert (
        "Overdue step (this machine's process log): task=CR-002 step=S2 "
        "activity=review deadline=2026-01-02T00:00:00+00:00 past="
    ) in err
    assert "task=CR-003" not in err


def test_a_step_inside_its_deadline_prints_no_overdue_step_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a step inside its deadline prints no overdue-step line."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _log_step(repo, "S1", deadline="2999-01-01T00:00:00+00:00")

    main(["doctor"])

    assert "Overdue step" not in capsys.readouterr().err


def test_an_overdue_step_never_makes_doctor_exit_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an overdue step never makes doctor exit non-zero."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _task(repo, "CR-001")
    _log_step(repo, "S1")

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    assert "Overdue step (this machine's process log): task=CR-001" in captured.err
    assert "Summary: all 10 checks passed" in captured.out


def test_an_unreadable_process_log_is_named_not_a_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unreadable process log is named, not a failure —
    a file where the directory should be."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _task(repo, "CR-001")
    state = _state(repo)
    state.root.mkdir(parents=True)
    state.log.write_text("not a directory\n", encoding="utf-8")

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    assert f"cannot read the process log {state.log} (not a directory)" in captured.err
    assert "Overdue step" not in captured.err
    assert "Summary: all 10 checks passed" in captured.out


def test_a_missing_process_log_reads_as_no_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a missing process log reads as no steps."""
    repo = _project(tmp_path, monkeypatch)
    _every_precondition_met(repo, monkeypatch)
    _task(repo, "CR-001")

    assert not _state(repo).log.exists()
    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    assert _paths_lines(repo) in captured.err
    assert "Overdue step" not in captured.err


def test_the_moment_taken_as_now_is_injectable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The moment the report judges deadlines against is injectable, so
    a test decides what has passed."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _log_step(repo, "S1", deadline="2030-01-01T00:00:00+00:00")

    late = io.StringIO()
    run_doctor(repo, stderr=late, now=datetime(2030, 6, 1, tzinfo=UTC))
    assert "Overdue step" in late.getvalue()

    early = io.StringIO()
    run_doctor(repo, stderr=early, now=datetime(2029, 6, 1, tzinfo=UTC))
    assert "Overdue step" not in early.getvalue()


def test_the_process_log_is_read_once_per_doctor_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the process log is read once per doctor run — once for
    all tasks, not once per task."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    _task(repo, "CR-002")
    _task(repo, "CR-003")
    calls: list[LocalState] = []

    def spy(state: LocalState) -> list[dict[str, object]]:
        calls.append(state)
        return read_events(state)

    monkeypatch.setattr(steps, "read_events", spy)

    main(["doctor"])
    capsys.readouterr()

    assert len(calls) == 1


def test_status_and_doctor_share_the_one_process_log_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``status`` and ``doctor`` read the process log through the one
    shared reader — ``read_process_events`` in ``steps.py`` — so a spy
    on the read it performs sees each command read once per run."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")
    calls: list[LocalState] = []

    def spy(state: LocalState) -> list[dict[str, object]]:
        calls.append(state)
        return read_events(state)

    monkeypatch.setattr(steps, "read_events", spy)

    main(["status"])
    main(["doctor"])
    capsys.readouterr()

    assert len(calls) == 2


def test_doctor_prints_the_three_paths_once_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: doctor prints the three paths once, on stderr."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")

    main(["doctor"])

    captured = capsys.readouterr()
    assert _paths_lines(repo) in captured.err
    for label in ("journal:", "process log:", "local state:"):
        assert captured.err.count(f"{label} ") == 1
        assert label not in captured.out


def test_each_path_prints_escaped_like_other_displayed_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: each path prints escaped like other displayed text."""
    repo = tmp_path / "jour\nnal"
    _init_repo(repo)
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    monkeypatch.chdir(repo)

    main(["doctor"])

    err = capsys.readouterr().err
    assert (
        "journal: "
        + escape_for_display(str(repo.resolve() / ".agentmarshal" / "journal"))
        in err
    )


def test_in_a_sidecar_the_paths_are_the_journal_repositorys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: in a sidecar the journal and local-state paths are the
    journal repository's."""
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    for directory in (host, sidecar):
        directory.mkdir()
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=directory,
            check=True,
            capture_output=True,
        )
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    capsys.readouterr()

    main(["doctor"])

    error_output = capsys.readouterr().err
    state = _state(sidecar)
    assert (
        f"journal: {sidecar.resolve() / '.agentmarshal' / 'journal'}\n"
        f"process log: {state.log}\n"
        f"local state: {state.root}\n"
    ) in error_output
    assert str(host.resolve()) not in error_output


def test_a_local_state_that_cannot_be_resolved_is_named_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a local state that cannot be resolved is named
    unavailable."""
    repo = _project(tmp_path, monkeypatch)
    _task(repo, "CR-001")

    def refuse(_placement: Placement) -> LocalState:
        raise LocalStateError(f"{repo}: git cannot name a common directory")

    monkeypatch.setattr(doctor, "local_state", refuse)

    main(["doctor"])

    err = capsys.readouterr().err
    assert f"journal: {repo.resolve() / '.agentmarshal' / 'journal'}\n" in err
    assert "process log: unavailable (" in err
    assert "local state: unavailable (" in err
    assert "git cannot name a common directory" in err


def test_a_project_that_cannot_be_found_marks_all_three_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a project that cannot be found marks all three
    unavailable."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    assert main(["doctor"]) == 1

    err = capsys.readouterr().err
    assert "journal: unavailable (" in err
    assert "process log: unavailable (" in err
    assert "local state: unavailable (" in err


def _versioned_git(output: str) -> object:
    """A ``subprocess.run`` stand-in answering *output* to ``--version``."""

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

    return run


def test_an_older_git_fails_the_check_naming_the_minimum_and_the_remedy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario: an older git fails the check naming the minimum and the
    remedy."""
    monkeypatch.setattr(subprocess, "run", _versioned_git("git version 2.30.9\n"))

    ok, detail = doctor._check_git_available(lambda _name: "git")

    assert not ok
    assert "2.30.9" in detail
    assert "2.31" in detail
    assert "upgrade git" in detail


def test_a_new_enough_git_passes_the_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario: a new-enough git passes the check."""
    for output in (
        "git version 2.31.0\n",
        "git version 2.47.3\n",
        "git version 3.0\n",
    ):
        monkeypatch.setattr(subprocess, "run", _versioned_git(output))

        ok, _detail = doctor._check_git_available(lambda _name: "git")

        assert ok, output


def test_the_version_parses_without_its_platform_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario: the version parses without its platform suffix."""
    monkeypatch.setattr(
        subprocess,
        "run",
        _versioned_git("git version 2.39.2.windows.1\n"),
    )

    ok, detail = doctor._check_git_available(lambda _name: "git")

    assert ok
    assert "2.39.2" in detail

    monkeypatch.setattr(
        subprocess,
        "run",
        _versioned_git("git version 2.30.0.windows.1\n"),
    )
    ok, detail = doctor._check_git_available(lambda _name: "git")
    assert not ok
    assert "2.31" in detail


def test_a_version_that_cannot_be_read_fails_the_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario: a version that cannot be read fails the check."""
    monkeypatch.setattr(subprocess, "run", _versioned_git("git version\n"))

    ok, detail = doctor._check_git_available(lambda _name: "git")

    assert not ok
    assert "2.31" in detail
    assert "upgrade git" in detail


def test_an_unreadable_version_is_judged_exactly_as_a_missing_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreadable ``git --version`` output is judged exactly as a
    missing git: the same ``git`` check fails either way — identical
    ``ok`` and identical standing as a check rather than a
    precondition — and the exit status follows those alone, so both
    runs exit alike."""
    repo = _project(tmp_path, monkeypatch)

    missing = next(
        result
        for result in run_doctor(
            repo, resolver=lambda _name: None, stderr=io.StringIO()
        )
        if result.name == "git"
    )
    monkeypatch.setattr(subprocess, "run", _versioned_git("git version\n"))
    unreadable = next(
        result
        for result in run_doctor(
            repo, resolver=lambda _name: "git", stderr=io.StringIO()
        )
        if result.name == "git"
    )

    assert (
        (missing.ok, missing.precondition)
        == (
            unreadable.ok,
            unreadable.precondition,
        )
        == (False, False)
    )
